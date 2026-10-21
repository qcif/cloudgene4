import argparse
import os

from django.core.management.base import BaseCommand, CommandError

from workflows import registry


class Command(BaseCommand):
    help = ('Declaratively install a workflow: make the apps[] entry match the given options, '
            'touching settings.yaml only if something differs. The last output line is '
            '"changed: <id>" or "unchanged: <id>".')

    def add_arguments(self, parser):
        parser.add_argument('path', help='App directory containing cloudgene.yaml, or the yaml '
                                         'file (relative paths: $CLOUDGENE_HOME/apps, then cwd)')
        parser.add_argument('--public', action=argparse.BooleanOptionalAction, default=False,
                            help='Accessible to every user (default: no)')
        parser.add_argument('--groups', default='', help='Comma-separated group names')
        parser.add_argument('--disabled', action='store_true', help='Keep the workflow disabled')
        parser.add_argument('--profile', default='', help='Nextflow -profile for this app')
        parser.add_argument('--work-dir', default='', help='Nextflow work dir for this app')
        parser.add_argument('--trust-output', action=argparse.BooleanOptionalAction, default=False,
                            help='Serve the job output as trusted HTML (default: no)')

    def handle(self, *args, **opts):
        path = opts['path']
        if not os.path.isabs(path) and os.path.exists(path):
            path = os.path.abspath(path)
        want = {
            'enabled': not opts['disabled'],
            'public': opts['public'],
            'groups': sorted({g.strip() for g in opts['groups'].split(',') if g.strip()}),
            'trust_output': opts['trust_output'],
        }
        want_nf = {'profile': opts['profile'].strip(), 'work_dir': opts['work_dir'].strip()}

        try:
            changed = self._ensure(path, want, want_nf)
        except registry.RegistryError as exc:
            detail = ''.join(f'\n  - {e}' for e in exc.errors if e != exc.message)
            raise CommandError(f'{exc.message}{detail}')
        self.stdout.write(f'{"changed" if changed else "unchanged"}: {self._app_id}')

    def _ensure(self, path, want, want_nf):
        yaml_path = registry.resolve_app_path(path)
        meta, _raw = registry.load_definition(yaml_path)
        self._app_id = meta.id
        changed = False

        current = next((st for st in registry.list_apps() if st.id == meta.id), None)
        if current is None:
            registry.install(path, enabled=want['enabled'], public=want['public'],
                             groups=want['groups'])
            changed = True
        elif os.path.abspath(current.yaml_path) != os.path.abspath(yaml_path):
            registry.install(path, replace=True)
            changed = True

        current = registry.get_status(meta.id)
        have = {key: getattr(current, key) for key in want}
        have['groups'] = sorted(current.groups)
        access = {key: value for key, value in want.items() if value != have[key]}
        if access:
            registry.update_access(meta.id, **access)
            changed = True
        nextflow = {key: value for key, value in want_nf.items() if value != getattr(current, key)}
        if nextflow:
            registry.set_nextflow_settings(meta.id, **nextflow)
            changed = True
        return changed
