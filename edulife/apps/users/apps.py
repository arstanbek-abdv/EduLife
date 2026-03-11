from django.apps import AppConfig


class DbAndUsersConfig(AppConfig):
    name = 'apps.users'
    
    def ready(self):
        import apps.users.signals
