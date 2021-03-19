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

import pytest
import json

from nomad.app.v1.models import WithQuery
from nomad.search import update_by_query
from nomad.search.v1 import search
from nomad.metainfo.elasticsearch_extension import entry_type, entry_index

from tests.utils import ExampleData


@pytest.fixture()
def example_data(elastic_module, raw_files_module, mongo_module, test_user, other_test_user):
    data = ExampleData(uploader=test_user)

    data.create_entry(
        upload_id='test_upload_id',
        calc_id='test_upload_id',
        mainfile='test_content/test_embargo_entry/mainfile.json',
        shared_with=[],
        with_embargo=True)

    data.save()


@pytest.fixture()
def indices(elastic):
    pass


def test_indices(indices):
    assert entry_type.quantities.get('entry_id') is not None
    assert entry_type.quantities.get('upload_id') is not None


@pytest.mark.parametrize('api_query, total', [
    pytest.param('{}', 1, id='empty'),
    pytest.param('{"results.method.simulation.program_name": "VASP"}', 1, id="match"),
    pytest.param('{"results.method.simulation.program_name": "VASP", "results.method.simulation.dft.xc_functional_type": "dne"}', 0, id="match_all"),
    pytest.param('{"and": [{"results.method.simulation.program_name": "VASP"}, {"results.method.simulation.dft.xc_functional_type": "dne"}]}', 0, id="and"),
    pytest.param('{"or":[{"results.method.simulation.program_name": "VASP"}, {"results.method.simulation.dft.xc_functional_type": "dne"}]}', 1, id="or"),
    pytest.param('{"not":{"results.method.simulation.program_name": "VASP"}}', 0, id="not"),
    pytest.param('{"results.method.simulation.program_name": {"all": ["VASP", "dne"]}}', 0, id="all"),
    pytest.param('{"results.method.simulation.program_name": {"any": ["VASP", "dne"]}}', 1, id="any"),
    pytest.param('{"results.method.simulation.program_name": {"none": ["VASP", "dne"]}}', 0, id="none"),
    pytest.param('{"results.method.simulation.program_name": {"gte": "VASP"}}', 1, id="gte"),
    pytest.param('{"results.method.simulation.program_name": {"gt": "A"}}', 1, id="gt"),
    pytest.param('{"results.method.simulation.program_name": {"lte": "VASP"}}', 1, id="lte"),
    pytest.param('{"results.method.simulation.program_name": {"lt": "A"}}', 0, id="lt"),
])
def test_search_query(indices, example_data, api_query, total):
    api_query = json.loads(api_query)
    results = search(owner='all', query=WithQuery(query=api_query).query)
    assert results.pagination.total == total  # pylint: disable=no-member


def test_update_by_query(indices, example_data):
    result = update_by_query(
        update_script='''
            ctx._source.entry_id = "other test id";
        ''',
        owner='all', query={}, index='v1')

    entry_index.refresh()

    assert result['updated'] == 1
    results = search(owner='all', query=dict(entry_id='other test id'))
    assert results.pagination.total == 1
