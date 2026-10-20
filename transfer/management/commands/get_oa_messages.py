import requests, json
from django.core.management.base import BaseCommand
from transfer.models import oaMessage
from transfer.utils import get_token, get_val, handle_mess
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
        
        self.total_messages = int(oa_messages['total'])
        return(oa_messages)
            

    def save_messages(self,messages):
        last_mess = 0
        already_here_count = 0
        for i, article in enumerate(messages['messages']):
            
            
            # check if messages are meant for us. the correct ror, if it's not a p2, if it's a duplicate.
            # put in a check to see if this particular message has been processed already
            if oaMessage.objects.filter(oa_id=article['id']):#this article exists already
                self.stdout.write('it\'s here already')
                already_here_count+=1
                if already_here_count>10: #if ten in a row are already saved. then we can probalby stop checking.
                    print('we got enough')
                    exit()
                continue
            elif article['type'] == "p2":
                self.stdout.write('it is p2.')
                continue
            elif article['header']['meta']['routing']['notification'] != "WEBHOOK":
                # this comes in as a webhook or EMAIL so we don't want to duplicate.
                continue
            # articles must be sent to the correct ROR id.
            elif article['header']['to']['address'] != settings.institution_ror:
                print(" not for us.")
                continue
                #########^^ these could be saved if we wanted to let oaswitchboard know about issues.
            
            # make the objs
            mess = oaMessage()
            mess.oa_id = article['id']
            mess.json = json.dumps(article)
            mess = handle_mess("begin", "beginning to process oa message.", mess)
            #make sure they have the proper major data fields.
            if get_val(article,'data') != 0:
                if get_val(article['data'],'article') != 0:
                    if get_val(article['data']['article'],'title') != 0:
                        mess.title = get_val(article['data']['article'],'title')
                    else:
                        mess.title='title field is missing'
                        handle_mess("error", "title field is missing", mess)
                        continue
                else:
                    mess.title = 'article field is missing.'
                    handle_mess("error", "article field is missing.", mess)
                    continue
            else:
                mess.title = 'data field is missing.'
                handle_mess("error", "data field is missing.")
                continue

            # oftentimes there are two articles coming in that are identical except for an irrelevant change in hash.
            # usually one after another. 
            if last_mess!=0 and mess.title == last_mess.title:
                # make the last mess a duplicate.
                handle_mess("duplicate", "this is a duplicate of the last message. should be ignored.", last_mess)
                
            
            if mess.status == "begin":
                mess.status = "oa-ready"
            if mess.note == "beginning to process oa message.":
                mess.note = "ok from oaSwitchboard."
            mess.save()
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
        