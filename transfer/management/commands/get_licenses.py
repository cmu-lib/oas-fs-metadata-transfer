from django.core.management.base import BaseCommand, CommandError
from transfer.models import repoLicense
from oafs.settings import secrets
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

        fs_token_response = requests.post('https://api.figsh.com/v2/token', headers=headers, json=json_data).json()
        self.stdout.write(json.dumps(fs_token_response))
        self.token = fs_token_response['token']

    def get_save_licenses(self):

        params = {
            'access_token': self.token, 
        }

        our_licenses = requests.get('https://api.figsh.com/v2/account/licenses', params=params).json()
        for l in our_licenses:
            repoLicense(url = l['url'],value=l['value'],name=l['name']).save()

            



    def handle(self, *args, **options):

        if self.token == "":
            self.get_token()
            
        self.get_save_licenses()
        
