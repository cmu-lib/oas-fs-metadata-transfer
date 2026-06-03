from django.core.management.base import BaseCommand, CommandError
from transfer.models import oaMessage,fsAttempt,repoLicense #,orcidUser
from oafs.settings import secrets, fs_base_url
import requests
import json
import re
from datetime import datetime



class Command(BaseCommand):
	orcid_match = re.compile("\d{4}-\d{4}-\d{4}-(\d{3}X|\d{4})")
	
	def get_val(self,dictionary,key): #stupid function for keyerror try catch.
		try:
			return dictionary[key]
		except KeyError:
			return  "" #empty string if it doesn't exist. you may wanna handle this differently.

	def add_to_note(self,message,note_addition,is_error):
		if message.note=="":
			message.note=note_addition+ " -- " + str(datetime.now())
		else:
			message.note+="\n"+note_addition + " -- " + str(datetime.now())
		if is_error:
			message.status='error'
			message.save()

	def convert_oa(self):
		ready_messages = oaMessage.objects.filter(status='ready')
		message_counter=0
		for message in ready_messages:
			mj = json.loads(message.message_json)
			# print(mj)
			message_counter+=1
			message_to_fs = {"authors":[],"funding_list":[],"title":"","published_date":"","status":"published","license":0,"doi":"","keywords":['OA Switchboard'],"defined_type":"journal contribution","group_id":secrets['figshare_group_id']}
			# let's get authors
			authors = mj['data']['authors']
			article_orcid_authors = []
			for this_guy in authors:
				# {
				# "id": 97657,
				# "full_name": "John Doe",
				# "first_name": "John",
				# "last_name": "Doe",
				# "is_active": 1,
				# "url_name": "John_Doe",
				# "orcid_id": "1234-5678-9123-1234"
				# }
				# ou = orcidUser()
				# ou.f_name = fn = self.get_val(this_guy,'firstName')
				# ou.l_name = ln = self.get_val(this_guy,'lastName')
				fn = self.get_val(this_guy,'firstName')
				ln = self.get_val(this_guy,'lastName')
				ini = self.get_val(this_guy,'initials')
				orcid = self.get_val(this_guy,'ORCID')
				ini = self.get_val(this_guy,'initials')
				orcid = self.get_val(this_guy,'ORCID')

				if "orcid.org" in orcid:
				    orcid = orcid.split('/')[3]
				    if self.orcid_match.match(orcid) is None or len(orcid.split('-'))>4:
				        orcid=""
				        self.add_to_note(message,"\ncouldn't find or improperly formatted orcid id for "+ fn + " " + ln,1)
				# inst = self.get_val(this_guy,'institutions')
				# print(inst) # ex [{'name': 'Departmentof Biomedical Engineering, Carnegie MellonUniversity, Pittsburgh, Pennsylvania, United States, 15213', 'country': '', 'sourceaffiliation': '', 'ror': 'https://ror.org/05x2bcf33'}]
				# inst = self.get_val(inst[0],'name').split(',')[0]
				# where does inst go??? i guess we won't use it!
				# ou.orcid = orcid
				# ou.save()
				# article_orcid_authors.append(ou)
				author_dict = {"name":fn+" "+ln,"first_name":fn,"last_name":ln,"orcid_id":orcid}
				message_to_fs['authors'].append(author_dict)
				

			article = mj['data']['article']
			print(article)
			print(message.id)
			title = article['title']
			message_to_fs['description'] = "This journal contribution is published Open Access by the publisher. Follow the DOI link to retrieve a copy of the full text.\n" + self.get_val(article,'acknowledgement')
			message_to_fs['title'] = title
			print(str(message.id) + title)
			if self.get_val(article,'manuscript'):
				publication_date = self.get_val(article['manuscript']['dates'],'publication')
			else:
				self.add_to_note(message,"theres no manuscript field which contains the publication date",1)
				continue
			# we need a publication date.
			if publication_date == "":
			    publication_date = self.get_val(article['manuscript']['dates'],'acceptance')
			    # this is the one time we add to note and don't change to error.
			    self.add_to_note(message,"using the 'acceptance date' because no publication date was found",0)
			    message.save()
			message_to_fs['published_date']=publication_date

			# get license.
			license = repoLicense.objects.filter(name=article['vor']['license'])
			if not license:
				message_to_fs['license']=44
				self.add_to_note(message,"using default license. there is no matching license. was looking for: " + article['vor']['license'],0)
				print("\nthere's no matching license here!!!!\n")
			else:
				print('yeah it matches')
				# confident in using [0] here because of unique constraint on the model
				message_to_fs['license']=int(license[0].value)

			# DOI DOI DOI
			message_to_fs['doi']=article['doi'][16:len(article['doi'])]

			#grant info.
			if len(self.get_val(article,'grants'))>0:

				for grant in article['grants']:
					print(grant)
					if len(self.get_val(grant,'name'))>0:
						message_to_fs['funding_list'].append({"grant_code":grant['name']})
					elif len(self.get_val(grant,'id'))>0:
						message_to_fs['funding_list'].append({"grant_code":grant['id']})
					else:
						message_to_fs['funding_list'].append({"grant_code":0})
						self.add_to_note(message,'could not determine grant code',1)


			fsa = fsAttempt(fs_attempt_json=json.dumps(message_to_fs), oama_fk=message)
			fsa.save()
			#save this attempt with the authors.
			for author in article_orcid_authors:
				author.articles.add(fsa)
				author.save()

	def handle(self, *args, **options):

		self.convert_oa()

