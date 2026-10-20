import os
import stat
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

from jobs import runner
from workflows.definition import Step

REMOTE_WORK_DIR = 'az://workdata/wf2'


class ResolveBinaryTests(TestCase):

    def test_found_in_fallback_dir_when_not_on_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / 'nextflow'
            exe.write_text('#!/bin/sh\n')
            exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
            with mock.patch.dict(os.environ, {'PATH': '/nonexistent'}), \
                    mock.patch.object(runner, 'NEXTFLOW_FALLBACK_DIRS', (tmp,)):
                self.assertEqual(runner.resolve_binary('nextflow'), str(exe))

    def test_unresolved_name_is_returned_unchanged(self):
        with mock.patch.dict(os.environ, {'PATH': '/nonexistent'}), \
                mock.patch.object(runner, 'NEXTFLOW_FALLBACK_DIRS', ()):
            self.assertEqual(runner.resolve_binary('nextflow'), 'nextflow')


class RemoteWorkDirTests(TestCase):

    def test_remote_uri_passes_through_without_a_local_path(self):
        job = SimpleNamespace(id=uuid.uuid4())
        self.assertEqual(runner.work_dir_for(job, REMOTE_WORK_DIR + '/'),
                         f'{REMOTE_WORK_DIR}/{job.id}')

    def test_is_remote_uri(self):
        self.assertTrue(runner.is_remote_uri('s3://bucket/x'))
        self.assertFalse(runner.is_remote_uri('relative/dir'))
        self.assertFalse(runner.is_remote_uri('/abs/dir'))


class ResolveScriptTests(TestCase):

    def test_existing_script_resolves_to_absolute_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'main.nf').write_text('')
            result = runner.resolve_script(Step(name='s'), Path(tmp))
            self.assertEqual(result, str((Path(tmp) / 'main.nf').resolve()))

    def test_missing_local_script_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'main.nf'):
                runner.resolve_script(Step(name='s'), Path(tmp))

    def test_remote_pipeline_name_passes_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = Step(name='s', script='nf-core/rnaseq')
            self.assertEqual(runner.resolve_script(step, Path(tmp)), 'nf-core/rnaseq')
