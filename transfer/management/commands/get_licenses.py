from django.core.management.base import BaseCommand, CommandError
from transfer.models import repoLicense
from oafs.settings import secrets, fs_base_url
import requests
import json



class Command(BaseCommand):
    token=""
    def get_token(self):
        headers = {
            'Content-Type': 'application/json',
        }

        json_data = {
            'client_id': secrets['figshare_client_id'],
            'client_secret': secrets['figshare_client_secret'],
            'grant_type': 'client_credentials',
        }

        fs_token_response = requests.post(fs_base_url+'token', headers=headers, json=json_data).json()
        self.stdout.write(json.dumps(fs_token_response))
        self.token = fs_token_response['token']

    def get_save_licenses(self):

        params = {
            'access_token': self.token, 
        }

        our_licenses = requests.get(fs_base_url+'account/licenses', params=params).json()

        for l in our_licenses:
            if repoLicense.objects.filter(name=l['name']).exists():
                continue
            else:
                repoLicense(url = l['url'],value=l['value'],name=l['name']).save()

            



    def handle(self, *args, **options):

        if self.token == "":
            self.get_token()
            
        self.get_save_licenses()
        
