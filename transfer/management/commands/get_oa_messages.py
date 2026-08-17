import requests, json
from django.core.management.base import BaseCommand
from transfer.models import oaMessage, messageStatus
from transfer.utils import get_token, get_val
from transfer import settings

#receive messages from OA SWITCHBOARD


class Command(BaseCommand):
    access = get_token('oaswitchboard')
    startrow = 1
    total_messages = 0
    messages = []
        
    def get_message_batch(self):
        headers = {
            'Authorization': 'Bearer ' + self.access.token
        }

        params = {
            'startrow': str(self.startrow),
            'maxrows': settings.how_many_oa_messages,
            'filter': 'all',
            'orderby': 'created',
            'orderdir': 'desc',
        }

        oa_messages = requests.get(self.access.url+'messages', params=params, headers=headers).json()
        
        # self.stdout.write(json.dumps(oa_messages))
        
        self.total_messages = int(oa_messages['total'])
        return(oa_messages)
            

    def save_messages(self,messages):
        last_mess = 0
        already_here_count = 0
        for i, article in enumerate(messages['messages']):
            # put in a check to see if this particular message has been processed already
            if oaMessage.objects.filter(oa_id=article['id']):#this article exists already
                self.stdout.write('it\'s here already')
                already_here_count+=1
                if already_here_count>5:
                    print('we got enough')
                    exit()
                continue
            elif article['type'] == "p2":
                self.stdout.write('it is p2.')
                continue
            if article['header']['meta']['routing']['notification'] != "WEBHOOK":
                # this comes in as a webhook or a EMAIL so we don't want to duplicate.
                continue
            mess_status = messageStatus()
            mess_status.status = "begin"
            mess_status.note = "beginning to process message."
            mess_status.save()
            mess = oaMessage()
            mess.oa_id = article['id']
            mess.json = json.dumps(article)
            mess.status=mess_status
            mess.save()
            
            # articles must be sent to the correct ROR id.
            if article['header']['to']['address'] != settings.institution_ror:
                print(" not for us.")
                mess_status.note = " not for us. meant for: "+ article['header']['to']['address']
                mess_status.status = "not-for-us"
                mess_status.save()
                mess.save()
                continue
            
            if get_val(article,'data') != '!!missing!!':
                if get_val(article['data'],'article') != '!!missing!!':
                    if get_val(article['data']['article'],'title') != '!!missing!!':
                        mess.title = get_val(article['data']['article'],'title')
                    else:
                        mess.title='title field is missing'
                        mess_status.note='title field is missing'
                        mess_status.status = 'error'
                else:
                    mess.title = 'article field is missing.'
                    mess_status.note = 'article field is missing.'
                    mess_status.status = "error"
            else:
                mess.title = 'data field is missing.'
                mess_status.note = 'data field is missing.'
                mess_status.status = "error"
            # self.stdout.write(self.get_val(self.get_val(self.get_val(article,'data'),'article'),'title'))

            # mess.title = self.get_val(self.get_val(self.get_val(article,'data'),'article'),'title')
            self.stdout.write(mess.title)

            # oftentimes there are two articles coming in that are identical except for a small change
            # one after another 
            if last_mess!=0 and mess.title == last_mess.title:
                print('same titles!!!!')
                self.stdout.write(mess.title)
                if article['created']>json.loads(last_mess.json)['created']:
                    last_mess.status.status="duplicate"
                    last_mess.status.save()
                else:
                    mess.status="duplicate"
                    mess_status.status = "duplicate"
                    mess_status.save()
            mess.save()
            if mess_status.status == "begin":
                mess_status.status = "oa-complete"
            if mess_status.note == "beginning to process message.":
                mess_status.note = "ok from oaSwitchboard."
            mess_status.save()
            last_mess = mess
            

            
    
    def add_arguments(self, parser):
        # parser.add_argument("poll_ids", nargs="+", type=int)
        parser.add_argument(
            "--all",
            action="store_true", #idk what this does :)
            help="go back and get all messages with multiple queries.",
        )

    def handle(self, *args, **options):
            
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
        