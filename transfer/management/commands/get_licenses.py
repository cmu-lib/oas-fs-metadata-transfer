import requests, json

from django.core.management.base import BaseCommand
from transfer.models import repoLicense
from transfer.utils import get_token

class Command(BaseCommand):

    access = get_token('figshare')

    def get_save_licenses(self):

        params = {
            'access_token': self.access['token'], 
        }

        our_licenses = requests.get(self.access['url']+'account/licenses', params=params).json()

        for l in our_licenses:
            if repoLicense.objects.filter(name=l['name']).exists():
                continue
            else:
                repoLicense(url = l['url'],value=l['value'],name=l['name']).save()


    def handle(self, *args, **options):
        self.get_save_licenses()
        
