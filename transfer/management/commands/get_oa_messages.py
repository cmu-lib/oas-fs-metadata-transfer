from django.core.management.base import BaseCommand, CommandError
from oafs.transfer.models import oaMessage
from oafs.settings import secrets
import requests
import json
# import tempfile.NamedTemporaryFile as ntf

#messages from OA SWITCHBOARD
#################
# oa_token first#
#################



class Command(BaseCommand):
    token = ""
    startrow = 1
    total_messages = 0
    messages = []

    def getval(self,dictionary,key): #stupid function for keyerror try catch.
        try:
            return dictionary[key]
        except KeyError:
            return  '!!missing!!'

    def get_token(self):
        headers = {
        'Content-Type': 'application/json',
        }

        json_data = {
            'email': secrets['oa_switchboard_email'],
            'password': secrets['oa_switchboard_pw'],
        }

        oa_token_response = requests.post('https://api.oaswitchboard.org/v2/authorize', headers=headers, json=json_data).json()
        self.stdout.write(json.dumps(oa_token_response))
        self.token = oa_token_response['token']

    def get_message_batch(self):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }

        params = {
            'startrow': str(self.startrow),
            'maxrows': '50',
            'filter': 'all',
            'orderby': 'created',
            'orderdir': 'desc',
        }

        oa_messages = requests.get('https://api.oaswitchboard.org/v2/messages', params=params, headers=headers).json()
        self.stdout.write(json.dumps(oa_messages))
        # if self.getval(oa_messages,'message') is True: #there was a message
        #     self.stdout.write("boooo something broke")
        #     self.stdout.write(getval(oa_messages,'message'))#write the error
        #     exit()
        # else:
        self.stdout.write(json.dumps(oa_messages))
        self.total_messages = int(oa_messages['total'])
        return(oa_messages)
            

    def save_messages(self,messages):
        for article in messages['messages']:
            # put in a check to see if this particular message exists already
            if oaMessage.objects.filter(message_id=article['id']):#this article exists already
                self.stdout.write('its here already')
                continue
            mess = oaMessage()
            mess.message_id = article['id']
            mess.message_json = str(article)
            mess.save()
            if self.getval(article,'data') != '!!missing!!':
                if self.getval(article['data'],'article') != '!!missing!!':
                    mess.message_title = self.getval(article['data']['article'],'title')
                else:
                    mess.message_title = 'article field is missing. how crazy'
            else:
                mess.message_title = 'data field is missing. how crazy'
            # self.stdout.write(self.getval(self.getval(self.getval(article,'data'),'article'),'title'))

            # mess.message_title = self.getval(self.getval(self.getval(article,'data'),'article'),'title')
            mess.save()
            

            
    
    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int)
        parser.add_argument(
            "--all",
            action="store_true",#idk what this does :)
            help="go back and get all messages with multiple queries.",
        )

    def handle(self, *args, **options):

        if self.token == "":
            self.get_token()
            
        if options["all"]:
            # get first batch of messages where total is also saved
            self.save_messages(self.get_message_batch())
            self.startrow+=50
            while self.startrow < self.total_messages:
                self.stdout.write('new batch of messages '+str(self.total_messages)+ ' total with startrow @: '+ str(self.startrow))
                self.save_messages(self.get_message_batch())
                self.startrow+=50
                
        else:
            self.save_messages(self.get_message_batch())
        
