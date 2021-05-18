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

'''
Uploads contains classes and functions to create and maintain file structures
for uploads.

There are two different structures for uploads in two different states: *staging* and *public*.
Possible operations on uploads differ based on this state. Staging is used for
processing, heavily editing, creating hashes, etc. Public is supposed to be a
almost readonly (beside metadata) storage.

.. code-block:: sh

    fs/staging/<upload>/raw/**
                       /archive/<calc>.json
    fs/public/<upload>/raw-public.plain.zip
                      /raw-restricted.plain.zip
                      /archive-public.json.zip
                      /archive-restricted.json.zip

There is an implicit relationship between files, based on them being in the same
directory. Each directory with at least one *mainfile* is a *calculation directory*
and all the files are *aux* files to that *mainfile*. This is independent of the
respective files actually contributing data or not. A *calculation directory* might
contain multiple *mainfile*. E.g., user simulated multiple states of the same system, have
one calculation based on the other, etc. In this case the other *mainfile* is an *aux*
file to the original *mainfile* and vice versa.

Published files are kept in pairs of public and restricted files. Here the multiple *mainfiles*
per directory provides a dilemma. If on *mainfile* is restricted, all its *aux* files
should be restricted too. But if one of the *aux* files is actually a *mainfile* it
might be published!

There are multiple ways to solve this. Due to the rarity of the case, we take the
most simple solution: if one file is public, all files are made public, execpt those
being other mainfiles. Therefore, the aux files of a restricted calc might become public!
'''

from abc import ABCMeta
import sys
from typing import IO, Generator, Dict, Iterable, Callable, List, Tuple, Any, NamedTuple
import os.path
import os
import shutil
import tarfile
import hashlib
import io
import pickle
import json

from nomad import config, utils, datamodel
from nomad.archive import write_archive, read_archive, ArchiveReader

# TODO this should become obsolete, once we are going beyong python 3.6. For now
# python 3.6's zipfile does not allow to seek/tell within a file-like opened from a
# file in a zipfile.
if sys.version_info >= (3, 7):
    import zipfile
else:
    import zipfile37 as zipfile

user_metadata_filename = 'user_metadata.pickle'


def always_restricted(path: str):
    '''
    Used to put general restrictions on files, e.g. due to licensing issues. Will be
    called during packing and while accessing public files.
    '''
    basename = os.path.basename(path)
    if basename.startswith('POTCAR') and not basename.endswith('.stripped'):
        return True


def copytree(src, dst):
    '''
    A close on ``shutils.copytree`` that does not try to copy the stats on all files.
    This is unecessary for our usecase and also causes permission denies for unknown
    reasons.
    '''
    os.makedirs(dst, exist_ok=False)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d)
        else:
            shutil.copyfile(s, d)


def create_tmp_dir(prefix: str) -> str:
    '''
    Creates a temporary directory in the directory specified by `config.fs.tmp`. The name
    of the directory will first be set to `prefix`, but if that name is already taken, a
    suffix will be added to ensure a completely clean, new directory is created. The full
    path to the created directory is returned.
    '''
    assert os.path.exists(config.fs.tmp)
    assert prefix and '/' not in prefix
    for index in range(1, 100):
        dir_name = prefix if index == 1 else f'{prefix}_{index}'
        path = os.path.join(config.fs.tmp, dir_name)
        try:
            os.makedirs(path)
            return path
        except FileExistsError:
            pass  # Try again with different suffix
    raise RuntimeError('Could not create temporary directory - too many directories with same prefix?')


class PathObject:
    '''
    Object storage-like abstraction for paths in general.
    Arguments:
        bucket: The bucket to store this object in
        object_id: The object id (i.e. directory path)
        os_path: Override the "object storage" path with the given path.
        prefix: Add a x-digit prefix directory, e.g. foo/test/ -> foo/tes/test
        create_prefix: Create the prefix right away
    '''
    def __init__(
            self, bucket: str, object_id: str, os_path: str = None,
            prefix: bool = False, create_prefix: bool = False) -> None:
        if os_path:
            self.os_path = os_path
        else:
            self.os_path = os.path.join(bucket, object_id)

        if prefix and config.fs.prefix_size > 0:
            segments = list(os.path.split(self.os_path))
            last = segments[-1]
            segments[-1] = last[:config.fs.prefix_size]
            segments.append(last)
            self.os_path = os.path.join(*segments)

            if create_prefix:
                os.makedirs(os.path.dirname(self.os_path), exist_ok=True)

    def delete(self) -> None:
        basename = os.path.basename(self.os_path)
        parent_directory = os.path.dirname(self.os_path)
        parent_name = os.path.basename(parent_directory)

        if os.path.isfile(self.os_path):
            os.remove(self.os_path)
        else:
            shutil.rmtree(self.os_path)

        if len(parent_name) == config.fs.prefix_size and basename.startswith(parent_name):
            try:
                if not os.listdir(parent_directory):
                    os.rmdir(parent_directory)
            except Exception as e:
                utils.get_logger(__name__).error(
                    'could not remove empty prefix dir', directory=parent_directory, exc_info=e)

    def exists(self) -> bool:
        return os.path.exists(self.os_path)

    @property
    def size(self) -> int:
        ''' The os determined file size. '''
        return os.stat(self.os_path).st_size

    def __repr__(self) -> str:
        return self.os_path


class DirectoryObject(PathObject):
    '''
    Object storage-like abstraction for directories.
    Arguments:
        bucket: The bucket to store this object in
        object_id: The object id (i.e. directory path)
        create: True if the directory structure should be created. Default is False.
    '''
    def __init__(self, bucket: str, object_id: str, create: bool = False, **kwargs) -> None:
        super().__init__(bucket, object_id, **kwargs)
        self._create = create
        if create and not os.path.isdir(self.os_path):
            os.makedirs(self.os_path)

    def join_dir(self, path, create: bool = None) -> 'DirectoryObject':
        if create is None:
            create = self._create
        return DirectoryObject(None, None, create=create, os_path=os.path.join(self.os_path, path))

    def join_file(self, path) -> PathObject:
        dirname = os.path.dirname(path)
        if dirname != '':
            return self.join_dir(dirname).join_file(os.path.basename(path))
        else:
            return PathObject(None, None, os_path=os.path.join(self.os_path, path))

    def exists(self) -> bool:
        return os.path.isdir(self.os_path)


class ExtractError(Exception):
    pass


class Restricted(Exception):
    pass


class UploadPathInfo(NamedTuple):
    '''
    Stores basic info about the object (file or folder) at some path relative to the
    upload root folder.
    '''
    path: str
    is_file: bool
    size: int
    access: str


class UploadFiles(DirectoryObject, metaclass=ABCMeta):

    def __init__(
            self, bucket: str, upload_id: str,
            is_authorized: Callable[[], bool] = lambda: False,
            create: bool = False) -> None:
        self.logger = utils.get_logger(__name__, upload_id=upload_id)

        super().__init__(bucket, upload_id, create=create, prefix=True)

        if not create and not self.exists():
            raise KeyError(upload_id)

        self.upload_id = upload_id
        self._is_authorized = is_authorized

    @property
    def _user_metadata_file(self):
        return self.join_file('user_metadata.pickle')

    @property
    def user_metadata(self) -> dict:
        if self._user_metadata_file.exists():
            with open(self._user_metadata_file.os_path, 'rb') as f:
                return pickle.load(f)

        else:
            return {}

    @user_metadata.setter
    def user_metadata(self, data: dict) -> None:
        with open(self._user_metadata_file.os_path, 'wb') as f:
            pickle.dump(data, f)

    def to_staging_upload_files(self, create: bool = False, **kwargs) -> 'StagingUploadFiles':
        ''' Casts to or creates corresponding staging upload files or returns None. '''
        raise NotImplementedError()

    @staticmethod
    def get(upload_id: str, *args, **kwargs) -> 'UploadFiles':
        if DirectoryObject(config.fs.staging, upload_id, prefix=True).exists():
            return StagingUploadFiles(upload_id, *args, **kwargs)
        elif DirectoryObject(config.fs.public, upload_id, prefix=True).exists():
            return PublicUploadFiles(upload_id, *args, **kwargs)
        else:
            return None

    def raw_path_is_well_formed(self, path: str) -> bool:
        '''
        Checks if a path is a well formed "raw path". These paths are relative to the
        raw file directory of an upload. All methods that expect raw path arguments should
        use this method to validate the well-formedness of the path.

        We only allow very simple paths to be used as raw paths. They may not start with
        '/' or contain '//' or '.' or '..' elements, for security reasons. They may end
        with a single '/', indicating that a folder is referred. For referring to the raw
        "root folder" itself, the empty string should be used, not '.' etc.
        '''
        if type(path) != str:
            return False
        if path == '':
            return True
        if path.startswith('/') or '//' in path:
            return False
        for element in path.split('/'):
            if element == '.' or element == '..':
                return False
        return True

    def raw_path_exists(self, path: str) -> bool:
        '''
        Returns True if the specified path is a valid raw path (either file or directory)
        '''
        raise NotImplementedError()

    def raw_path_is_file(self, path: str) -> bool:
        '''
        Returns True if the specified path points to a file (rather than a directory).
        '''
        raise NotImplementedError()

    def raw_directory_list(self, path: str, recursive=False, files_only=False) -> Iterable[UploadPathInfo]:
        '''
        Returns an iterator of UploadPathInfo objects for each element (file or folder) in
        the directory specified by `path`. If `recursive` is set to True, subdirectories are
        also crawled. If `files_only` is set, only the file objects found are returned.
        If path is not a valid directory, the result will be empty.
        '''
        raise NotImplementedError()

    def raw_file(self, file_path: str, *args, **kwargs) -> IO:
        '''
        Opens a raw file and returns a file-like object. Additional args, kwargs are
        delegated to the respective `open` call.
        Arguments:
            file_path: The path to the file relative to the upload.
        Raises:
            KeyError: If the file does not exist.
            Restricted: If the file is restricted and upload access evaluated to False.
        '''
        raise NotImplementedError()

    def raw_file_size(self, file_path: str) -> int:
        '''
        Returns:
            The size of the given raw file.
        '''
        raise NotImplementedError()

    def raw_file_manifest(self, path_prefix: str = None) -> Generator[str, None, None]:
        '''
        Returns the path for all raw files in the archive (with a given prefix).
        Arguments:
            path_prefix: An optional prefix; only returns those files that have the prefix.
        Returns:
            An iterable over all (matching) raw files.
        '''
        raise NotImplementedError()

    def read_archive(self, calc_id: str, access: str = None) -> ArchiveReader:
        '''
        Returns an :class:`nomad.archive.ArchiveReader` that contains the
        given calc_id. Both restricted and public archive are searched by default.
        The optional ``access`` parameter can be used to limit this lookup to the
        ``public`` or ``restricted`` archive.'''
        raise NotImplementedError()

    def close(self):
        ''' Release possibly held system resources (e.g. file handles). '''
        pass


class StagingUploadFiles(UploadFiles):
    def __init__(
            self, upload_id: str, is_authorized: Callable[[], bool] = lambda: False,
            create: bool = False) -> None:
        super().__init__(config.fs.staging, upload_id, is_authorized, create)

        self._raw_dir = self.join_dir('raw')
        self._archive_dir = self.join_dir('archive')
        self._frozen_file = self.join_file('.frozen')

        self._size = 0
        self._shared = DirectoryObject(config.fs.public, upload_id, create=create)

    def to_staging_upload_files(self, create: bool = False, **kwargs) -> 'StagingUploadFiles':
        return self

    @property
    def size(self) -> int:
        return self._size

    def _file(self, path_object: PathObject, *args, **kwargs) -> IO:
        try:
            return open(path_object.os_path, *args, **kwargs)
        except FileNotFoundError:
            raise KeyError(path_object.os_path)
        except IsADirectoryError:
            raise KeyError(path_object.os_path)

    def raw_path_exists(self, path: str) -> bool:
        if not self.raw_path_is_well_formed(path):
            return False
        return os.path.exists(os.path.join(self._raw_dir.os_path, path))

    def raw_path_is_file(self, path: str) -> bool:
        if not self.raw_path_is_well_formed(path):
            return False
        return os.path.isfile(os.path.join(self._raw_dir.os_path, path))

    def raw_directory_list(self, path: str, recursive=False, files_only=False) -> Iterable[UploadPathInfo]:
        if not self.raw_path_is_well_formed(path):
            return
        os_path = os.path.join(self._raw_dir.os_path, path)
        if not os.path.isdir(os_path):
            return
        for element_name in sorted(os.listdir(os_path)):
            element_raw_path = os.path.join(path, element_name)
            element_os_path = os.path.join(os_path, element_name)
            is_file = os.path.isfile(element_os_path)
            if not files_only or is_file:
                size = os.stat(element_os_path).st_size if is_file else -1
                yield UploadPathInfo(
                    path=element_raw_path,
                    is_file=is_file,
                    size=size,
                    access='unpublished')
            if recursive and not is_file:
                for sub_path_info in self.raw_directory_list(element_raw_path, recursive, files_only):
                    yield sub_path_info

    def raw_file(self, file_path: str, *args, **kwargs) -> IO:
        assert self.raw_path_is_well_formed(file_path)
        if not self._is_authorized():
            raise Restricted
        return self._file(self.raw_file_object(file_path), *args, **kwargs)

    def raw_file_size(self, file_path: str) -> int:
        assert self.raw_path_is_well_formed(file_path)
        if not self._is_authorized():
            raise Restricted
        return self.raw_file_object(file_path).size

    def raw_file_object(self, file_path: str) -> PathObject:
        assert self.raw_path_is_well_formed(file_path)
        return self._raw_dir.join_file(file_path)

    def write_archive(self, calc_id: str, data: Any) -> int:
        ''' Writes the data as archive file and returns the archive file size. '''
        archive_file_object = self.archive_file_object(calc_id)
        try:
            write_archive(archive_file_object.os_path, 1, data=[(calc_id, data)])
        except Exception as e:
            # in case of failure, remove the possible corrupted archive file
            if archive_file_object.exists():
                archive_file_object.delete()

            raise e

        return self.archive_file_object(calc_id).size

    def read_archive(self, calc_id: str, access: str = None) -> ArchiveReader:
        if not self._is_authorized():
            raise Restricted

        try:
            return read_archive(self.archive_file_object(calc_id).os_path)

        except FileNotFoundError:
            raise KeyError(calc_id)

    def archive_file_object(self, calc_id: str) -> PathObject:
        return self._archive_dir.join_file('%s.%s' % (calc_id, 'msg'))

    def add_rawfiles(
            self, path: str, target_dir: str = '', cleanup_source_file_and_dir: bool = False) -> None:
        '''
        Adds the file or folder specified by `path` to this upload, in the raw directory
        specified by `target_dir`. If `path` denotes a zip or tar archive file, it will
        first be extracted to a temporary directory. The file(s) are *merged* with the
        existing upload files, i.e. new files are added, replacing old files if there
        already exists file(s) by the same names, the rest of the old files are left
        untouched.

        Cleanup
        The method is responsible for trying to clean up temporarily extracted files.
        If `cleanup_source_file_and_dir` is True, the source file (defined by `path`), and
        its parent directory (which we also assume is temporary) are also cleaned up.
        Note: the cleanup steps are always carried out, also if the operation fails.

        Arguments:
            path: OS path to a file or folder to add.
            target_dir: A raw path (i.e. path relative to the raw directory) defining
                where the resource defined by `path` should be put. If `target_dir` is not
                specified, it defaults to the empty string, i.e. the upload's raw dir.
            cleanup_source_file_and_dir: If true, the source file (defined by `path`) and
                its parent folder are included in the cleanup step - i.e. they are always
                deleted. Use when the file is stored temporarily.
        '''
        tmp_dir = None
        try:
            assert not self.is_frozen
            assert os.path.exists(path), f'{path} does not exist'
            assert self.raw_path_is_well_formed(target_dir)
            self._size += os.stat(path).st_size

            is_dir = os.path.isdir(path)
            if is_dir:
                is_zipfile = is_tarfile = False
            else:
                is_zipfile = zipfile.is_zipfile(path)
                is_tarfile = tarfile.is_tarfile(path)
                if is_zipfile or is_tarfile:
                    tmp_dir = create_tmp_dir(self.upload_id.replace(os.path.sep, '_'))
                    if is_zipfile:
                        with zipfile.ZipFile(path) as zf:
                            zf.extractall(tmp_dir)
                    elif is_tarfile:
                        with tarfile.open(path) as tf:
                            tf.extractall(tmp_dir)

            # Determine what to merge
            elements_to_merge: Iterable[Tuple[str, List[str], List[str]]] = []
            if is_dir or is_zipfile or is_tarfile:
                # Directory
                source_dir = path if is_dir else tmp_dir
                elements_to_merge = os.walk(source_dir)
            else:
                # Single file
                source_dir = os.path.dirname(path)
                elements_to_merge = [(source_dir, [], [os.path.basename(path)])]

            # Ensure target_dir exists and is a directory. If one of the elements in the
            # directory chain is a file, it needs to be deleted (the regular os.makedirs
            # doesn't do that).
            target_dir_subpath = self._raw_dir.os_path
            for dir_name in target_dir.split(os.path.sep):
                target_dir_subpath = os.path.join(target_dir_subpath, dir_name)
                if os.path.isfile(target_dir_subpath):
                    os.remove(target_dir_subpath)
                if not os.path.isdir(target_dir_subpath):
                    os.makedirs(target_dir_subpath)

            # Do the merge
            for root, dirs, files in elements_to_merge:
                elements = dirs + files
                os_target_dir = os.path.join(self._raw_dir.os_path, target_dir)
                for element in elements:
                    element_source_path = os.path.join(root, element)
                    element_relative_path = os.path.relpath(element_source_path, source_dir)
                    element_target_path = os.path.join(os_target_dir, element_relative_path)
                    if os.path.islink(element_source_path):
                        continue  # Skip links, could pose security risk
                    if os.path.exists(element_target_path):
                        if not (os.path.isdir(element_source_path) and os.path.isdir(element_target_path)):
                            # Target already exists and needs to be deleted
                            if os.path.isdir(element_target_path):
                                shutil.rmtree(element_target_path)
                            else:
                                os.remove(element_target_path)
                    # Copy or move the element
                    if os.path.isdir(element_source_path):
                        # Directory - just create corresponding directory in the target if needed.
                        if not os.path.exists(element_target_path):
                            os.makedirs(element_target_path)
                    else:
                        # File - copy or move it
                        if cleanup_source_file_and_dir or is_zipfile or is_tarfile:
                            # Move the file
                            shutil.move(element_source_path, element_target_path)
                        else:
                            # Copy the file
                            shutil.copyfile(element_source_path, element_target_path)
        finally:
            # Cleanup
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            if cleanup_source_file_and_dir:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                parent_dir = os.path.dirname(path)
                if os.path.exists(parent_dir):
                    shutil.rmtree(parent_dir)

    @property
    def is_frozen(self) -> bool:
        ''' Returns True if this upload is already *bagged*. '''
        return self._frozen_file.exists()

    def pack(
            self, entries: Iterable[datamodel.EntryMetadata], target_dir: DirectoryObject = None,
            skip_raw: bool = False, skip_archive: bool = False) -> None:
        '''
        Replaces the staging upload data with a public upload record by packing all
        data into files. It is only available if upload *is_bag*.
        This is potentially a long running operation.

        Arguments:
            upload: The upload with all calcs and  calculation metadata of the upload
                used to determine what files to pack and what the embargo situation is.
            target_dir: optional DirectoryObject to override where to put the files. Default
                is the corresponding public upload files directory.
            skip_raw: determine to not pack the raw data, only archive and user metadata
            skip_raw: determine to not pack the archive data, only raw and user metadata
        '''
        self.logger.info('started to pack upload')

        # freeze the upload
        assert not self.is_frozen, "Cannot pack an upload that is packed, or packing."
        with open(self._frozen_file.os_path, 'wt') as f:
            f.write('frozen')

        # create a target dir in the public bucket
        if target_dir is None:
            target_dir = DirectoryObject(
                config.fs.public, self.upload_id, create=True, prefix=True,
                create_prefix=True)
        assert target_dir.exists()

        def create_zipfile(access: str):
            return zipfile.ZipFile(
                PublicUploadFiles._create_raw_file_object(target_dir, access).os_path,
                mode='w')

        def write_msgfile(access: str, size: int, data: Iterable[Tuple[str, Any]]):
            file_object = PublicUploadFiles._create_msg_file_object(target_dir, access)
            write_archive(file_object.os_path, size, data)

        # zip archives
        if not skip_archive:
            with utils.timer(self.logger, 'packed msgpack archive') as log_data:
                restricted, public = self._pack_archive_files(entries, write_msgfile)
                log_data.update(restricted=restricted, public=public)

        # zip raw files
        if not skip_raw:
            with utils.timer(self.logger, 'packed raw files'):
                self._pack_raw_files(entries, create_zipfile)

    def _pack_archive_files(self, entries: Iterable[datamodel.EntryMetadata], write_msgfile):
        restricted, public = 0, 0
        for calc in entries:
            if calc.with_embargo:
                restricted += 1
            else:
                public += 1

        def create_iterator(with_embargo: bool):
            for calc in entries:
                if with_embargo == calc.with_embargo:
                    archive_file = self.archive_file_object(calc.calc_id)
                    if archive_file.exists():
                        data = read_archive(archive_file.os_path)[calc.calc_id].to_dict()
                        yield (calc.calc_id, data)
                    else:
                        yield (calc.calc_id, {})

        try:
            write_msgfile('public', public, create_iterator(False))
            write_msgfile('restricted', restricted, create_iterator(True))

        except Exception as e:
            self.logger.error('exception during packing archives', exc_info=e)

        return restricted, public

    def _pack_raw_files(self, entries: Iterable[datamodel.EntryMetadata], create_zipfile):
        raw_public_zip = create_zipfile('public')
        raw_restricted_zip = create_zipfile('restricted')

        try:
            # 1. add all public raw files
            # 1.1 collect all public mainfiles and aux files
            public_files: Dict[str, str] = {}
            for calc in entries:
                if not calc.with_embargo:
                    mainfile = calc.mainfile
                    assert mainfile is not None
                    # mainfile might already have been added due to being a auxfile to another calc
                    if mainfile not in public_files:
                        for filepath in self.calc_files(mainfile, with_cutoff=False):
                            if not always_restricted(filepath):
                                public_files[filepath] = None
            # 1.2 remove the non public mainfiles that have been added as auxfiles of public mainfiles
            for calc in entries:
                if calc.with_embargo:
                    mainfile = calc.mainfile
                    assert mainfile is not None
                    if mainfile in public_files:
                        del(public_files[mainfile])
            # 1.3 zip all remaining public
            for filepath in public_files.keys():
                raw_public_zip.write(self._raw_dir.join_file(filepath).os_path, filepath)

            # 2. everything else becomes restricted
            for filepath in self.raw_file_manifest():
                if filepath not in public_files:
                    raw_restricted_zip.write(self._raw_dir.join_file(filepath).os_path, filepath)

        except Exception as e:
            self.logger.error('exception during packing raw files', exc_info=e)

        finally:
            raw_restricted_zip.close()
            raw_public_zip.close()

    def raw_file_manifest(self, path_prefix: str = None) -> Generator[str, None, None]:
        upload_prefix_len = len(self._raw_dir.os_path) + 1
        for root, _, files in os.walk(self._raw_dir.os_path):
            for file in files:
                path = os.path.join(root, file)[upload_prefix_len:]
                if path_prefix is None or path.startswith(path_prefix):
                    yield path

    def calc_files(self, mainfile: str, with_mainfile: bool = True, with_cutoff: bool = True) -> Iterable[str]:
        '''
        Returns all the auxfiles and mainfile for a given mainfile. This implements
        nomad's logic about what is part of a calculation and what not. The mainfile
        is first entry, the rest is sorted.
        Arguments:
            mainfile: The mainfile relative to upload
            with_mainfile: Do include the mainfile, default is True
        '''
        mainfile_object = self._raw_dir.join_file(mainfile)
        if not mainfile_object.exists():
            raise KeyError(mainfile)

        mainfile_basename = os.path.basename(mainfile)
        calc_dir = os.path.dirname(mainfile_object.os_path)
        calc_relative_dir = calc_dir[len(self._raw_dir.os_path) + 1:]

        file_count = 0
        aux_files: List[str] = []
        for filename in os.listdir(calc_dir):
            if filename != mainfile_basename and os.path.isfile(os.path.join(calc_dir, filename)):
                aux_files.append(os.path.join(calc_relative_dir, filename))
                file_count += 1

            if with_cutoff and file_count > config.auxfile_cutoff:
                # If there are two many of them, its probably just a directory with lots of
                # calculations. In this case it does not make any sense to provide thousands of
                # aux files.
                break

        aux_files = sorted(aux_files)

        if with_mainfile:
            return [mainfile] + aux_files
        else:
            return aux_files

    def calc_id(self, mainfile: str) -> str:
        '''
        Calculates a id for the given calc.
        Arguments:
            mainfile: The mainfile path relative to the upload that identifies the calc in the folder structure.
        Returns:
            The calc id
        Raises:
            KeyError: If the mainfile does not exist.
        '''
        return utils.hash(self.upload_id, mainfile)

    def calc_hash(self, mainfile: str) -> str:
        '''
        Calculates a hash for the given calc based on file contents and aux file contents.
        Arguments:
            mainfile: The mainfile path relative to the upload that identifies the calc in the folder structure.
        Returns:
            The calculated hash
        Raises:
            KeyError: If the mainfile does not exist.
        '''
        hash = hashlib.sha512()
        for filepath in self.calc_files(mainfile):
            with open(self._raw_dir.join_file(filepath).os_path, 'rb') as f:
                for data in iter(lambda: f.read(65536), b''):
                    hash.update(data)

        return utils.make_websave(hash)

    def delete(self, include_public=True) -> None:
        super().delete()
        if self._shared.exists() and include_public:
            self._shared.delete()


class ArchiveBasedStagingUploadFiles(StagingUploadFiles):
    '''
    :class:`StagingUploadFiles` based on a single uploaded archive file (.zip)

    Arguments:
        upload_path: The path to the uploaded file.
    '''

    def __init__(
            self, upload_id: str, upload_path: str, *args, **kwargs) -> None:
        super().__init__(upload_id, *args, **kwargs)
        self.upload_path = upload_path

    @property
    def is_valid(self) -> bool:
        if self.upload_path is None:
            return False
        if not os.path.exists(self.upload_path):
            return False
        elif not os.path.isfile(self.upload_path):
            return False
        else:
            return True

    def extract(self) -> None:
        assert next(self.raw_file_manifest(), None) is None, 'can only extract once'
        super().add_rawfiles(self.upload_path)

    def add_rawfiles(self, *args, **kwargs) -> None:
        assert False, 'do not add_rawfiles to a %s' % self.__class__.__name__


class PublicUploadFilesBasedStagingUploadFiles(StagingUploadFiles):
    '''
    :class:`StagingUploadFiles` based on a single uploaded archive file (.zip)

    Arguments:
        upload_path: The path to the uploaded file.
    '''

    def __init__(
            self, public_upload_files: 'PublicUploadFiles', *args, **kwargs) -> None:
        super().__init__(public_upload_files.upload_id, *args, **kwargs)
        self.public_upload_files = public_upload_files

    def extract(self, include_archive: bool = False) -> None:
        assert next(self.raw_file_manifest(), None) is None, 'can only extract once'
        for access in ['public', 'restricted']:
            raw_file_zip = self.public_upload_files.raw_file_object(access)
            if raw_file_zip.exists():
                super().add_rawfiles(raw_file_zip.os_path)

            if include_archive:
                with self.public_upload_files._open_msg_file(access) as archive:
                    for calc_id, data in archive.items():
                        calc_id = calc_id.strip()
                        self.write_archive(calc_id, data.to_dict())

    def add_rawfiles(self, *args, **kwargs) -> None:
        assert False, 'do not add_rawfiles to a %s' % self.__class__.__name__

    def pack(self, entries: Iterable[datamodel.EntryMetadata], *args, **kwargs) -> None:
        '''
        Packs only the archive contents and stores it in the existing public upload files.
        '''
        super().pack(entries, target_dir=self.public_upload_files, skip_raw=True)


class PublicUploadFiles(UploadFiles):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(config.fs.public, *args, **kwargs)
        self._directories: Dict[str, Dict[str, UploadPathInfo]] = None
        self._raw_zip_files: Dict[str, zipfile.ZipFile] = {}
        self._archive_msg_files: Dict[str, ArchiveReader] = {}

    def close(self):
        for f in self._raw_zip_files.values():
            f.close()

        for f in self._archive_msg_files.values():
            f.close()

    @staticmethod
    def _create_raw_file_object(dir: DirectoryObject, access: str, suffix: str = '') -> PathObject:
        return dir.join_file(f'raw-{access}{suffix}.plain.zip')

    def raw_file_object(self, access: str, **kwargs) -> PathObject:
        return PublicUploadFiles._create_raw_file_object(self, access, **kwargs)

    def _open_raw_file(self, access: str) -> zipfile.ZipFile:
        if access in self._raw_zip_files:
            return self._raw_zip_files[access]

        zip_path = self.raw_file_object(access).os_path
        f = zipfile.ZipFile(zip_path)
        self._raw_zip_files[access] = f

        return f

    @staticmethod
    def _create_msg_file_object(dir: DirectoryObject, access: str, suffix: str = '') -> PathObject:
        if config.fs.archive_version_suffix:
            return dir.join_file(
                f'archive-{access}{suffix}-{config.fs.archive_version_suffix}.msg.msg')

        return dir.join_file(f'archive-{access}{suffix}.msg.msg')

    def msg_file_object(self, access: str, **kwargs) -> PathObject:
        return PublicUploadFiles._create_msg_file_object(self, access, **kwargs)

    def _open_msg_file(self, access: str) -> ArchiveReader:
        if access in self._archive_msg_files:
            archive = self._archive_msg_files[access]
            if not archive.is_closed():
                return archive

        msg_object = self.msg_file_object(access)

        if not msg_object.exists():
            raise FileNotFoundError()

        archive = read_archive(msg_object.os_path)
        assert archive is not None
        self._archive_msg_files[access] = archive

        return archive

    def to_staging_upload_files(self, create: bool = False, **kwargs) -> 'StagingUploadFiles':
        exists = False
        try:
            staging_upload_files = PublicUploadFilesBasedStagingUploadFiles(
                self, is_authorized=lambda: True)
            exists = True
        except KeyError:
            if not create:
                return None

            staging_upload_files = PublicUploadFilesBasedStagingUploadFiles(
                self, create=True, is_authorized=lambda: True)
            staging_upload_files.extract(**kwargs)

        if exists and create:
            raise FileExistsError('Staging upload does already exist')

        return staging_upload_files

    def add_metadata_file(self, metadata: dict):
        zip_path = self.raw_file_object('public').os_path
        with zipfile.ZipFile(zip_path, 'a') as zf:
            with zf.open('nomad.json', 'w') as f:
                f.write(json.dumps(metadata).encode())

    def _parse_content(self):
        '''
        Parses the content of files and folders and caches it in self._directories for
        faster future access.
        '''
        if self._directories is None:
            self._directories = dict()
            for access in ['public', 'restricted']:
                try:
                    zf = self._open_raw_file(access)
                    for path in zf.namelist():
                        file_name = os.path.basename(path)
                        directory_path = os.path.dirname(path)
                        # Ensure that all parent directories are added
                        sub_path = ''
                        for directory in directory_path.split(os.path.sep):
                            sub_path_content = self._directories.setdefault(sub_path, {})
                            sub_path_ext = os.path.join(sub_path, directory)

                            if directory not in sub_path_content:
                                sub_path_content[directory] = UploadPathInfo(
                                    path=sub_path_ext, is_file=False, size=-1, access=access)
                            sub_path = sub_path_ext

                        if file_name:
                            directory_content = self._directories.setdefault(directory_path, {})
                            directory_content[file_name] = UploadPathInfo(
                                path=path,
                                is_file=True,
                                size=zf.getinfo(path).file_size,
                                access=access)
                except FileNotFoundError:
                    pass

    def raw_path_exists(self, path: str) -> bool:
        if not self.raw_path_is_well_formed(path):
            return False
        self._parse_content()
        explicit_directory_path = path.endswith(os.path.sep)
        path = path.rstrip(os.path.sep)
        base_name = os.path.basename(path)
        directory_path = os.path.dirname(path)
        directory_content = self._directories.get(directory_path)
        if directory_content is not None:
            if not base_name:
                return True
            if base_name in directory_content:
                path_info = directory_content[base_name]
                if path_info.access == 'public' or self._is_authorized():
                    if explicit_directory_path and path_info.is_file:
                        return False
                    return True
        return False

    def raw_path_is_file(self, path: str) -> bool:
        if not self.raw_path_is_well_formed(path):
            return False
        self._parse_content()
        base_name = os.path.basename(path)
        directory_path = os.path.dirname(path)
        if not base_name:
            return False  # Requested path is an explicit directory path
        directory_content = self._directories.get(directory_path)
        if directory_content and base_name in directory_content:
            path_info = directory_content[base_name]
            if path_info.access == 'public' or self._is_authorized():
                return path_info.is_file
        return False

    def raw_directory_list(self, path: str, recursive=False, files_only=False) -> Iterable[UploadPathInfo]:
        if not self.raw_path_is_well_formed(path):
            return
        self._parse_content()
        path = path.rstrip(os.path.sep)
        directory_content = self._directories.get(path)
        if directory_content is not None:
            for __, path_info in sorted(directory_content.items()):
                if path_info.access == 'public' or self._is_authorized():
                    if not files_only or path_info.is_file:
                        yield path_info
                if recursive and not path_info.is_file:
                    for sub_path_info in self.raw_directory_list(path_info.path, recursive, files_only):
                        yield sub_path_info

    @property
    def public_raw_data_file(self):
        return self.raw_file_object('public').os_path

    def raw_file(self, file_path: str, *args, **kwargs) -> IO:
        mode = kwargs.get('mode') if len(args) == 0 else args[0]
        if 'mode' in kwargs:
            del(kwargs['mode'])
        mode = mode if mode else 'rb'

        for access in ['public', 'restricted']:
            try:
                zf = self._open_raw_file(access)
                f = zf.open(file_path, 'r', **kwargs)

                if (access == 'restricted' or always_restricted(file_path)) and not self._is_authorized():
                    raise Restricted

                if 't' in mode:
                    return io.TextIOWrapper(f)
                else:
                    return f
            except FileNotFoundError:
                pass
            except IsADirectoryError:
                pass
            except KeyError:
                pass

        raise KeyError(file_path)

    def raw_file_size(self, file_path: str) -> int:
        for access in ['public', 'restricted']:
            try:
                zf = self._open_raw_file(access)
                info = zf.getinfo(file_path)
                if (access == 'restricted' or always_restricted(file_path)) and not self._is_authorized():
                    raise Restricted

                return info.file_size
            except FileNotFoundError:
                pass
            except KeyError:
                pass

        raise KeyError(file_path)

    def raw_file_manifest(self, path_prefix: str = None) -> Generator[str, None, None]:
        for access in ['public', 'restricted']:
            try:
                zf = self._open_raw_file(access)
                for path in zf.namelist():
                    if path_prefix is None or path.startswith(path_prefix):
                        yield path
            except FileNotFoundError:
                pass

    def read_archive(self, calc_id: str, access: str = None) -> Any:
        if access is not None:
            accesses = [access]
        else:
            accesses = ['public', 'restricted']

        for access in accesses:
            try:
                archive = self._open_msg_file(access)
                if calc_id in archive:
                    if access == 'restricted' and not self._is_authorized():
                        raise Restricted

                    return archive
            except FileNotFoundError:
                pass

        raise KeyError(calc_id)

    def re_pack(
            self, entries: Iterable[datamodel.EntryMetadata], skip_raw: bool = False,
            skip_archive: bool = False) -> None:
        '''
        Replaces the existing public/restricted data file pairs with new ones, based
        on current restricted information in the metadata. Should be used after updating
        the restrictions on calculations. This is potentially a long running operation.
        '''
        # compute a list of files to repack
        files = []

        for access in ['public', 'restricted']:
            if not skip_archive:
                files.append((
                    self.msg_file_object(access, suffix='repacked'),
                    self.msg_file_object(access)))
            if not skip_raw:
                files.append((
                    self.raw_file_object(access, suffix='repacked'),
                    self.raw_file_object(access)))

        # check if there already is a running repack
        for repacked_file, _ in files:
            if repacked_file.exists():
                raise FileExistsError('Repacked files already exist')

        # create staging files
        staging_upload = self.to_staging_upload_files(create=True, include_archive=True)

        def create_zipfile(access: str) -> zipfile.ZipFile:
            file = self.raw_file_object(access, suffix='repacked')
            return zipfile.ZipFile(file.os_path, mode='w')

        def write_msgfile(access: str, size: int, data: Iterable[Tuple[str, Any]]):
            file = self.msg_file_object(access, suffix='repacked')
            write_archive(file.os_path, size, data)

        # perform the repacking
        try:
            if not skip_archive:
                # staging_upload._pack_archive_files(entries, create_zipfile)
                staging_upload._pack_archive_files(entries, write_msgfile)
            if not skip_raw:
                staging_upload._pack_raw_files(entries, create_zipfile)
        finally:
            staging_upload.delete()

        # replace the original files with the repacked ones
        for repacked_file, public_file in files:
            shutil.move(
                repacked_file.os_path,
                public_file.os_path)
