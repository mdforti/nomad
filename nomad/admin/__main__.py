# Copyright 2018 Markus Scheidgen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an"AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import logging
import os
import sys
import shutil
from elasticsearch_dsl import A

from nomad import config as nomad_config, infrastructure, processing
from nomad.search import Search


@click.group(help='''The nomad admin command to do nasty stuff directly on the databases.
                     Remember: With great power comes great responsibility!''')
@click.option('-v', '--verbose', help='sets log level to info', is_flag=True)
@click.option('--debug', help='sets log level to debug', is_flag=True)
@click.option('--config', help='the config file to use')
def cli(verbose: bool, debug: bool, config: str):
    if config is not None:
        nomad_config.load_config(config_file=config)

    if debug:
        nomad_config.console_log_level = logging.DEBUG
    elif verbose:
        nomad_config.console_log_level = logging.INFO
    else:
        nomad_config.console_log_level = logging.WARNING

    nomad_config.service = os.environ.get('NOMAD_SERVICE', 'admin')
    infrastructure.setup_logging()


@cli.command(help='Runs tests and linting. Useful before commit code.')
@click.option('--skip-tests', help='Do not test, just do code checks.', is_flag=True)
def qa(skip_tests: bool):
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    ret_code = 0
    if not skip_tests:
        click.echo('Run tests ...')
        ret_code += os.system('python -m pytest -svx tests')
    click.echo('Run code style checks ...')
    ret_code += os.system('python -m pycodestyle --ignore=E501,E701 nomad tests')
    click.echo('Run linter ...')
    ret_code += os.system('python -m pylint --load-plugins=pylint_mongoengine nomad tests')
    click.echo('Run static type checks ...')
    ret_code += os.system('python -m mypy --ignore-missing-imports --follow-imports=silent --no-strict-optional nomad tests')

    sys.exit(ret_code)


@cli.command(help='Checks consistency of files and es vs mongo and deletes orphan entries.')
@click.option('--dry', is_flag=True, help='Do not delete anything, just check.')
@click.option('--skip-fs', is_flag=True, help='Skip cleaning the filesystem.')
@click.option('--skip-es', is_flag=True, help='Skip cleaning the es index.')
def clean(dry, skip_fs, skip_es):
    infrastructure.setup_logging()
    infrastructure.setup_mongo()
    infrastructure.setup_elastic()

    if not skip_fs:
        upload_dirs = []
        for bucket in [nomad_config.fs.public, nomad_config.fs.staging]:
            for prefix in os.listdir(nomad_config.fs.public):
                for upload in os.listdir(os.path.join(nomad_config.fs.public, prefix)):
                    upload_dirs.append((upload, os.path.join(nomad_config.fs.public, prefix, upload)))

        to_delete = list(
            path for upload, path in upload_dirs
            if processing.Upload.objects(upload_id=upload).first() is None)

        if not dry and len(to_delete) > 0:
            input('Will delete %d upload directories. Press any key to continue ...' % len(to_delete))

            for path in to_delete:
                shutil.rmtree(path)
        else:
            print('Found %d upload directories with no upload in mongo.' % len(to_delete))

    if not skip_es:
        search = Search(index=nomad_config.elastic.index_name)
        search.aggs.bucket('uploads', A('terms', field='upload_id', size=12000))
        response = search.execute()

        to_delete = list(
            (bucket.key, bucket.doc_count)
            for bucket in response.aggregations.uploads.buckets
            if processing.Upload.objects(upload_id=bucket.key).first() is None)

        calcs = 0
        for _, upload_calcs in to_delete:
            calcs += upload_calcs

        if not dry and len(to_delete) > 0:
            input(
                'Will delete %d calcs in %d uploads from ES. Press any key to continue ...' %
                (calcs, len(to_delete)))
            for upload, _ in to_delete:
                Search(index=nomad_config.elastic.index_name).query('term', upload_id=upload).delete()
        else:
            print('Found %d calcs in %d uploads from ES with no upload in mongo.' % (calcs, len(to_delete)))


if __name__ == '__main__':
    cli()  # pylint: disable=E1120
