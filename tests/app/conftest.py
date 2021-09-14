#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import List, Dict, Any
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from nomad import infrastructure, config, files
from nomad.archive import write_partial_archive_to_mongo
from nomad.app.main import app
from nomad.datamodel import EntryArchive, EntryMetadata, DFTMetadata, User
from nomad import processing as proc
from tests.test_files import create_test_upload_files


def create_auth_headers(user: User):
    return {
        'Authorization': 'Bearer %s' % user.user_id
    }


@pytest.fixture(scope='module')
def test_user_auth(test_user: User):
    return create_auth_headers(test_user)


@pytest.fixture(scope='module')
def other_test_user_auth(other_test_user: User):
    return create_auth_headers(other_test_user)


@pytest.fixture(scope='module')
def admin_user_auth(admin_user: User):
    return create_auth_headers(admin_user)


@pytest.fixture(scope='session')
def client():
    return TestClient(app, base_url='http://testserver/')


class ExampleData:
    def __init__(self, dft: dict = None, **kwargs):
        self.uploads: Dict[str, Dict[str, Any]] = dict()
        self.dict_upload_to_entry_ids: Dict[str, List[str]] = dict()
        self.entries: Dict[str, EntryMetadata] = dict()
        self.archives: Dict[str, EntryArchive] = dict()

        self.entry_defaults = kwargs
        self.dft_defaults = dft

        self._time_stamp = datetime.now()

    def save(self, with_files: bool = True, with_mongo: bool = True, with_es: bool = True):
        # save to elastic and mongo
        for upload_id, upload_dict in self.uploads.items():
            if with_mongo:
                mongo_upload = proc.Upload(**upload_dict)
                mongo_upload.save()

        for entry_metadata in self.entries.values():
            if with_mongo:
                mongo_entry = proc.Calc(
                    create_time=self._next_time_stamp(),
                    calc_id=entry_metadata.calc_id,
                    upload_id=entry_metadata.upload_id,
                    mainfile=entry_metadata.mainfile,
                    parser='parsers/vasp',
                    tasks_status='SUCCESS')
                mongo_entry.apply_entry_metadata(entry_metadata)
                mongo_entry.save()

            if with_es:
                entry_metadata.a_elastic.index()

        if with_es:
            infrastructure.elastic_client.indices.refresh(index=config.elastic.index_name)

        # create upload files
        if with_files:
            for upload_id, entry_ids in self.dict_upload_to_entry_ids.items():
                if upload_id in self.uploads:
                    published = self.uploads[upload_id]['published']
                else:
                    published = True
                archives = []
                for entry_id in entry_ids:
                    published &= self.entries[entry_id].published
                    if entry_id in self.archives:
                        archives.append(self.archives[entry_id])

                create_test_upload_files(upload_id, archives, published=published)

    def cleanup_files(self):
        '''
        If you have saved this ExampleData with with_files = True, us this method to clean
        up any created files from the system.
        '''
        for upload_id in self.uploads:
            upload_files = files.UploadFiles.get(upload_id)
            if upload_files and upload_files.exists():
                upload_files.delete()

    def _create_upload(self, upload_id, **kwargs):
        '''
        Creates a dictionary holding all the upload information.
        Default values are used/generated, and can be set via kwargs.
        '''
        upload_dict = {
            'upload_id': upload_id,
            'current_task': 'cleanup',
            'tasks_status': 'SUCCESS',
            'current_process': 'process_upload',
            'process_status': 'COMPLETED',
            'errors': [],
            'warnings': [],
            'create_time': self._next_time_stamp(),
            'upload_time': self._next_time_stamp(),
            'complete_time': self._next_time_stamp(),
            'published': False,
            'published_to': []}
        upload_dict.update(kwargs)
        if 'user_id' not in upload_dict and 'uploader' in self.entry_defaults:
            upload_dict['user_id'] = self.entry_defaults['uploader'].user_id
        self.uploads[upload_id] = upload_dict

    def _create_entry(
            self,
            calc_id: str, upload_id: str, mainfile: str,
            dft: dict = None, archive: dict = None, **kwargs):

        entry_archive = EntryArchive()
        entry_metadata = entry_archive.m_create(EntryMetadata)
        entry_metadata.m_update(
            calc_id=calc_id,
            upload_id=upload_id,
            mainfile=mainfile,
            calc_hash='dummy_hash_' + calc_id,
            domain='dft',
            upload_time=self._next_time_stamp(),
            published=True,
            processed=True,
            with_embargo=False,
            atoms=['H', 'O'],
            n_atoms=2,
            parser_name='parsers/vasp')
        entry_metadata.m_update(**self.entry_defaults)
        entry_metadata.m_update(**kwargs)

        section_dft = entry_metadata.m_create(DFTMetadata)
        section_dft.m_update(
            code_name='VASP',
            xc_functional='GGA',
            system='bulk')
        if self.dft_defaults is not None:
            section_dft.m_update(**self.dft_defaults)
        if dft is not None:
            section_dft.m_update(**dft)

        entry_archive.m_update_from_dict(dict(
            section_run=[{}],
            section_workflow={}))
        if archive is not None:
            entry_archive.m_update(**archive)

        entry_id = entry_metadata.calc_id
        self.archives[entry_id] = entry_archive
        self.entries[entry_id] = entry_metadata
        self.dict_upload_to_entry_ids.setdefault(upload_id, []).append(entry_id)

    def _next_time_stamp(self):
        '''
        Returns self._time_stamp and ticks up the time stamp with 1 millisecond. This
        utility guarantees that we get unique and increasing time stamps for each entity.
        '''
        self._time_stamp += timedelta(milliseconds=1)
        return self._time_stamp


@pytest.fixture(scope='module')
def example_data(elastic_module, raw_files_module, mongo_module, test_user, other_test_user, normalized):
    '''
    Provides a couple of uploads and entries including metadata, raw-data, and
    archive files.

    23 published without embargo
    1 unpublished
    1 unpublished shared
    1 published with embargo
    1 published shared with embargo

    partial archive exists only for id_01
    raw files and archive file for id_02 are missing
    id_10, id_11 reside in the same directory
    '''

    data = ExampleData(
        uploader=test_user,
        dft=dict(optimade=normalized.section_metadata.dft.optimade)
    )

    # one upload with two calc published with embargo, one shared
    data._create_upload(
        upload_id='id_embargo',
        name='name_embargo',
        published=True)
    data._create_entry(
        upload_id='id_embargo',
        calc_id='id_embargo',
        mainfile='test_content/test_embargo_entry/mainfile.json',
        shared_with=[],
        with_embargo=True)
    data._create_entry(
        upload_id='id_embargo',
        calc_id='id_embargo_shared',
        mainfile='test_content/test_embargo_entry_shared/mainfile.json',
        shared_with=[other_test_user],
        with_embargo=True)

    # one upload with two calc in staging, one shared
    data._create_upload(
        upload_id='id_unpublished',
        published=False)
    data._create_entry(
        upload_id='id_unpublished',
        calc_id='id_unpublished',
        mainfile='test_content/test_entry/mainfile.json',
        with_embargo=False,
        shared_with=[],
        published=False)
    data._create_entry(
        upload_id='id_unpublished',
        calc_id='id_unpublished_shared',
        mainfile='test_content/test_entry_shared/mainfile.json',
        shared_with=[other_test_user],
        with_embargo=False,
        published=False)

    # one upload with 23 calcs published
    data._create_upload(
        upload_id='id_published',
        name='name_published',
        published=True)
    for i in range(1, 24):
        entry_id = 'id_%02d' % i
        mainfile = 'test_content/subdir/test_entry_%02d/mainfile.json' % i
        if i == 11:
            mainfile = 'test_content/subdir/test_entry_10/mainfile_11.json'
        data._create_entry(
            upload_id='id_published',
            calc_id=entry_id,
            mainfile=mainfile)

        if i == 2:
            del(data.archives[entry_id])
        if i == 1:
            archive = data.archives[entry_id]
            write_partial_archive_to_mongo(archive)

    # one upload, no calcs, still processing
    data._create_upload(
        upload_id='id_processing',
        published=False,
        tasks_status='RUNNING',
        process_status='RUNNING')

    # one upload, no calcs, unpublished
    data._create_upload(
        upload_id='id_empty',
        published=False)

    data.save()
    yield data
    data.cleanup_files()


@pytest.fixture(scope='function')
def example_data_writeable(mongo, test_user, normalized):
    data = ExampleData(
        uploader=test_user,
        dft=dict(optimade=normalized.section_metadata.dft.optimade)
    )

    # one upload with one entry, published
    data._create_upload(
        upload_id='id_published_w',
        published=True)
    data._create_entry(
        upload_id='id_published_w',
        calc_id='id_published_w_entry',
        mainfile='test_content/test_embargo_entry/mainfile.json',
        shared_with=[],
        with_embargo=True)

    # one upload with one entry, unpublished
    data._create_upload(
        upload_id='id_unpublished_w',
        published=False)
    data._create_entry(
        upload_id='id_unpublished_w',
        calc_id='id_unpublished_w_entry',
        mainfile='test_content/test_embargo_entry/mainfile.json',
        shared_with=[],
        with_embargo=True)

    # one upload, no entries, still processing
    data._create_upload(
        upload_id='id_processing_w',
        published=False,
        tasks_status='RUNNING',
        process_status='RUNNING')

    # one upload, no entries, unpublished
    data._create_upload(
        upload_id='id_empty_w',
        published=False)

    data.save()
    yield
    data.cleanup_files()