from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from enote.sync import make_sync

class Command(BaseCommand):
    def handle(self, username, *args, **kw):
        user = User.objects.get(username=username)
        make_sync(user)
