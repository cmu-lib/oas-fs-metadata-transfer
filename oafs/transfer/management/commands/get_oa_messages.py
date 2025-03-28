from django.core.management.base import BaseCommand, CommandError
from transfer.models import oaMessage
from oafs.settings import secrets
import requests
import json
# import tempfile.NamedTemporaryFile as ntf

#messages from OA SWITCHBOARD
#################
# oa_token first#
#################



class Command(BaseCommand):
    

    def handle(self, *args, **options):
        self.stdout.write("penis")
        headers = {
            'Content-Type': 'application/json',
        }

        json_data = {
            'email': secrets['oa_switchboard_email'],
            'password': secrets['oa_switchboard_pw'],
        }

        oa_token_response = requests.post('https://api.oaswitchboard.org/v2/authorize', headers=headers, json=json_data).json()
        self.stdout.write(json.dumps(oa_token_response))
        oa_token = oa_token_response['token']

        # congrats you got a token.

        headers = {
            'Authorization': 'Bearer ' + oa_token
        }

        params = {
            'startrow': '1',
            'maxrows': '25',
            'filter': 'all',
            'orderby': 'created',
            'orderdir': 'desc',
        }

        oa_messages = requests.get('https://api.oaswitchboard.org/v2/messages', params=params, headers=headers).json()
        self.stdout.write(json.dumps(oa_messages))
        
        for article in oa_messages['messages']:
            mess = oaMessage()
            self.stdout.write(article['data']['article']['title'])
            mess.message_title = article['data']['article']['title']
            mess.message_id = article['id']
            mess.message_json = str(article)

            mess.save()

