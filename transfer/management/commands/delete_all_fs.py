from django.core.management.base import BaseCommand, CommandError
import requests
from oafs.settings import secrets, fs_base_url
import json

class Command(BaseCommand):
    token = ""
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
        

    def delete(self,all):
        headers = {
        'Content-Type': 'application/json',
        }

        params = {
            'access_token': self.token,
        }

        json_data = {}

        response = requests.post('https://api.figsh.com/v2/account/articles/search', params=params, headers=headers, json=json_data).json()

        for x in response:
            print(x['id'])
            response = requests.delete('https://api.figsh.com/v2/account/articles/'+str(x['id']),params=params,headers=headers)
            print(response.__dict__)
            print('goodbye, dirtbag')

    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int)
        parser.add_argument(
            "--all",
            action="store_true",#idk what this does :)
            help="delete all the last ones in there",
        )

    def handle(self, *args, **options):

        if self.token == "":
            self.get_token()
            
        if options["all"]:
            # get first batch of messages where total is also saved
            self.delete('all')    
        else:
            self.delete()
        
