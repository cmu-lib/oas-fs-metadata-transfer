from django.core.management.base import BaseCommand, CommandError
from transfer.models import oaMessage
from oafs.settings import secrets,how_many_oa_messages
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
        # self.token = 'eyJraWQiOiJ4RFdkTGJMWXZNb2hNSVhXTkF5bkwrenU3RzJ0dUY5RmFSMlplbVRNOTdRPSIsImFsZyI6IlJTMjU2In0.eyJjdXN0b206dHlwZSI6Imluc3RpdHV0aW9uIiwiY3VzdG9tOnJvciI6IjAwMDAwMDAiLCJzdWIiOiJlZDAyNjNiNi0zMzdjLTRkYWItOWIzNS0zZTQxYzc1NmEyYTgiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiY3VzdG9tOndlYmhvb2siOiJmYWxzZSIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS1jZW50cmFsLTEuYW1hem9uYXdzLmNvbVwvZXUtY2VudHJhbC0xX3A2WUlIUEpBTyIsImNvZ25pdG86dXNlcm5hbWUiOiJjbXVsaWJhcUBhbmRyZXcuY211LmVkdSIsImN1c3RvbTpwdWJzd2VldF9pZCI6IjAwMDAwMDAiLCJhdWQiOiI1ZmV0ajc1NWozNDdpYzA4OGlkMmIzc2hqciIsImN1c3RvbTppbnN0aXR1dGlvbiI6IkNhcm5lZ2llIE1lbGxvbiBVbml2ZXJzaXR5IiwiZXZlbnRfaWQiOiJlZjNiNzJiMC1lMmFjLTRjYzQtYmFlMS1kYWVmM2E0ZWQ2ZDEiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc0NjQ3ODIwNCwibmFtZSI6IkNhcm5lZ2llIE1lbGxvbiBVbml2ZXJzaXR5IiwiY3VzdG9tOnBlcnNpc3RlbnQiOiIxIiwiZXhwIjoxNzQ2NDgxODA0LCJpYXQiOjE3NDY0NzgyMDQsImVtYWlsIjoiY211bGliYXFAYW5kcmV3LmNtdS5lZHUifQ.CpOPSotRpVoT94OhxWHSK5-6di9f0wAYJo5mruKTxIfM-s_B3jaOtCi1wh-ZDjt12S_h4VLcfU1z0hWu0035oGBRzQlmFtC5oOLEO0sCG0imXyQjEhQRKM3kMy7bIYdeYrSPFmSMPZZYzjxeQ4rSHRrkcq3o6ZAYoM2mZ7QXs8vUQzx8LpuhZ1j6Vm0EwvyXXsD30EELlkOC47Aach-ID1hNCaErr--VFu3TAwsPqKvIOfQ3RdoL3WNsLqeU0cqeKhX_AuIvNFeTRmHDwWNtJwn5xpEUDFXM7YxRHq6AcSn7-oJE_AMtr1HntDsXHv2aRKxQmm6swveT6lW9DK3diw'

    def get_message_batch(self):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }

        params = {
            'startrow': str(self.startrow),
            'maxrows': how_many_oa_messages,
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
        # self.stdout.write(json.dumps(oa_messages))
        self.total_messages = int(oa_messages['total'])
        return(oa_messages)
            

    def save_messages(self,messages):
        last_mess = 0
        for i, article in enumerate(messages['messages']):
            # put in a check to see if this particular message exists already
            if oaMessage.objects.filter(message_id=article['id']):#this article exists already
                self.stdout.write('its here already')
                continue
            elif article['type'] == "p2":
                self.stdout.write('it is p2.')
                continue
            mess = oaMessage()
            mess.message_id = article['id']
            mess.message_json = json.dumps(article)
            # print(type(article))
            # print(json.dumps(article))
            mess.save()
            if self.getval(article,'data') != '!!missing!!':
                if self.getval(article['data'],'article') != '!!missing!!':
                    if self.getval(article['data']['article'],'title') != '!!missing!!':
                        mess.message_title = self.getval(article['data']['article'],'title')
                    else:
                        mess.message_title='title field is missing'
                        mess.note='title field is missing'
                        mess.status = 'error'
                else:
                    mess.message_title = 'article field is missing.'
                    mess.note = 'article field is missing.'
                    mess.status = "error"
            else:
                mess.message_title = 'data field is missing.'
                mess.note = 'data field is missing.'
                mess.status = "error"
            # self.stdout.write(self.getval(self.getval(self.getval(article,'data'),'article'),'title'))

            # mess.message_title = self.getval(self.getval(self.getval(article,'data'),'article'),'title')
            self.stdout.write(mess.message_title)

            # oftentimes there are two articles coming in that are identical except for a small change
            # one after another 
            if last_mess!=0 and mess.message_title == last_mess.message_title:
                print('same titles!!!!')
                self.stdout.write(mess.message_title)
                if article['created']>json.loads(last_mess.message_json)['created']:
                    last_mess.status="duplicate"
                    last_mess.save()
                else:
                    mess.status="duplicate"
            mess.save()
            last_mess = mess
            

            
    
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
        