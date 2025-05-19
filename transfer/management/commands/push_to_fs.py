from django.core.management.base import BaseCommand, CommandError
from transfer.models import oaMessage,fsAttempt,repoLicense
from oafs.settings import secrets, fs_base_url, my_ass
import requests
import json
import re
import time
from datetime import datetime

class Command(BaseCommand):
	token="6b062365841c10a3c38a8fda4f5704674118e84d546b8b3a8b128ca9efae7ceb86a377759f8cf8d4fe106974776f849be444f1684017bd221e495379142b5d59"
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
		print(self.token)

	def cleanup(self,article_id): # figshare automatically adds myself as a user to articles. 
		# i didn't write the thing so get me out of there.
		print('deleting publishing user')
		headers = {
			'Content-Type': 'application/json',
		}
		params = {
			'access_token': self.token,
		}
		response = requests.delete(fs_base_url+"account/articles/"+str(article_id)+"/authors/"+my_ass,params=params,headers=headers)
		print(response.__dict__)
		response = requests.post(fs_base_url+"account/articles/"+str(article_id)+"/private_links",params=params,headers=headers).json()
		print('private link here. if all goes well:')
		print(response['html_location'])
		return(response['html_location'])
		


	def push_messages(self):
		into_messages = fsAttempt.objects.filter(status='ready-for-push')
		headers = {
		    'Content-Type': 'application/json',
		}

		params = {
		    'access_token': self.token,
		}

		for i in into_messages:
			print(i.oama_fk)
			# print(int(json.loads(i.fs_attempt_json)['license']))
			# json.loads(i.fs_attempt_json)['license'] = int(json.loads(i.fs_attempt_json)['license'])
			response = requests.post(fs_base_url+'account/articles', params=params, headers=headers, data=i.fs_attempt_json).json()
			print(response) 
			# exit()
			try:
			    code = response['code'] #only on error is there a code thrown.
			    if response['code'] in ['UnknownException', 'BadRequest', 'UnprocessableEntity']:
			        print('NO ARTICLE WAS SAVED OMG')
			        print(response)
			        i.response = response['code']
			        i.status = 'failed'
			        i.note = response['message']
			        i.save()
			except KeyError:
				i.fs_id = response['entity_id']
				i.status='ready-for-review'
				print("oh boy i think it went in!")
				print(response)
				# for article in articles:
				i.link = self.cleanup(response['entity_id']) #returns link to article directly
				i.save()
		    

			    # article_up = str(response['entity_id'])

			# f = open("confirmed_article_ids.txt", "a")
			# f.write(article_up+',')
			# f.close()
			time.sleep(1)

	def add_arguments(self, parser):
		parser.add_argument(
			"--all",
			action="store_true",#idk what this does and doesn't show up in documentation :)
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
			self.push_messages()



