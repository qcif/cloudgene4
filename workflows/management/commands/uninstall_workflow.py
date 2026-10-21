from django.core.management.base import BaseCommand, CommandError

from workflows import registry


class Command(BaseCommand):
    help = ('Remove a workflow from settings.yaml apps[] (its files stay on disk). The last '
            'output line is "changed: <id>" or "unchanged: <id>".')

    def add_arguments(self, parser):
        parser.add_argument('id', help='Workflow id')
        parser.add_argument('--missing-ok', action='store_true',
                            help='Succeed (unchanged) if the workflow is not installed')

    def handle(self, *args, **opts):
        app_id = opts['id']
        try:
            registry.get_status(app_id)
        except registry.RegistryError as exc:
            if opts['missing_ok']:
                self.stdout.write(f'unchanged: {app_id}')
                return
            raise CommandError(exc.message)
        registry.uninstall(app_id)
        self.stdout.write(f'changed: {app_id}')
