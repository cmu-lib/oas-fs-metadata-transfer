from django.core.management.base import BaseCommand
from transfer.models import fsAttempt
from transfer.utils import get_token, handle_mess
from transfer. settings import figshare_user
import json, time, requests
from datetime import datetime

class Command(BaseCommand):
	access = get_token('oafigshare')
	
	def update_messages(self):
		upd_messages = fsAttempt.objects.filter(status='update')
		print(upd_messages)
		headers = {
		    'Content-Type': 'application/json',
		}

		params = {
		    'access_token': self.access.token,
		}

		for i in upd_messages:
			print("updating " + str(i.oam_fk))
			response = requests.put(self.access.url+'account/articles/'+str(i.fs_id), params=params, headers=headers, data=i.json).json()
			print(response) 
			# handle the code.
			try:
				code = response['code'] #only on error is there a code thrown.
				if response['code'] in ['UnknownException', 'BadRequest', 'UnprocessableEntity']:
					print('NO ARTICLE WAS SAVED OMG')
					print(response)
					i.response = response['code']
					i = handle_mess('failed during push',response['message'],i)
					i.oam_fk.status='failed during push'
					i.oam_fk.note = "\n failed at update:" + response['code']
					i.oam_fk.save()
					print(response)

				else:
					i.fs_id = response['entity_id']
					i = handle_mess('ready-for-review','article was saved',i)
					i.oam_fk.status='done'
					i.oam_fk.save()
					print(response)
					# for article in articles:
					self.cleanup(response['entity_id'],i.doi) #returns link to article directly
					# i.save()
					continue
			except KeyError: #do i need a try except? idr.
				i.fs_id = response['entity_id'] 
				i = handle_mess('ready-for-review','article was saved',i)
				i.oam_fk.status='done'
				i.oam_fk.save()
				print(response)
				# for article in articles:
				self.cleanup(response['entity_id'],i.doi) #returns link to article directly
				# i.save()

			time.sleep(1) #take a nap.

	def add_arguments(self, parser):
		# probably won't use all.
		parser.add_argument(
			"--all",
			action="store_true",#idk what this does and doesn't show up in documentation :)
			help="go back and get all messages with multiple queries.",
		)

	def handle(self, *args, **options):

		self.update_messages()



