from django.core.management.base import BaseCommand, CommandError
from transfer.models import oaMessage,fsAttempt,repoLicense #,orcidUser
from oafs.settings import secrets, fs_base_url, in_copyright_num
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
			return  ""

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
			already_subbed = False
			mj = json.loads(message.message_json)

			message_counter+=1
			article = mj['data']['article']
			title = article['title']
			new_doi = article['doi'][16:len(article['doi'])]
			
			message_to_fs = {"authors":[],"funding_list":[],"title":"","published_date":"","status":"published","license":0,"doi":new_doi,"keywords":['OA Switchboard'],"defined_type":"journal contribution","group_id":secrets['figshare_group_id']}

			message_to_fs['description'] = "This journal contribution is published Open Access by the publisher. Follow the DOI link to retrieve a copy of the full text.\n" + self.get_val(article,'acknowledgement')
			message_to_fs['title'] = title
			
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
				fn = self.get_val(this_guy,'firstName')
				ln = self.get_val(this_guy,'lastName')
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
				

			
			# print(str(message.id) + title)
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
				message_to_fs['license']= in_copyright_num
				self.add_to_note(message,"using default license. there is no matching license. was looking for: " + article['vor']['license'],0)
				print("\nthere's no matching license here!!!!\n")
			else:
				print('yeah it matches')
				# confident in using [0] here because of unique constraint on the model
				message_to_fs['license']=int(license[0].value)

			

			#grant info.
			if len(self.get_val(article,'grants'))>0:

				for grant in article['grants']:
					# print(grant)
					if len(self.get_val(grant,'name'))>0:
						message_to_fs['funding_list'].append({"grant_code":grant['name']})
					elif len(self.get_val(grant,'id'))>0:
						message_to_fs['funding_list'].append({"grant_code":grant['id']})
					else:
						message_to_fs['funding_list'].append({"grant_code":0})
						self.add_to_note(message,'could not determine grant code',1)

			message_to_fs['status']='ready-for-push'

			# check to see if this doi has gone in before. 
			# also apparently someone can resubmit the article months later...
			# if it hasn't gone in with the changes then we should 
			# - call the old one a duplicate on oamessage
			# - change status of fsattempt from ready-for-push to failed
			# - add this one.
			# if it HAS gone in 
			# ... update the old one based on the ID. must test this

			if self.get_val(mj['header']['meta'],'resubmitted'):
				# this is a resubmission. did we already upload it?
				print('this is a resubmission. for real....' + title)
				#get the old attempt
				old_fsAttempt = fsAttempt.objects.filter(doi=new_doi)
				print(old_fsAttempt)
				print('this is old attempts')
				#this is any old attempt that has the same doi.
				# do i need to check this stuff? i think everything goes in automatically. i think we should 
				# just overwrite it / set it for update.
				###################oldcode below
				# if old_fsAttempt.status=='ready-for-review' or old_fsAttempt.status=='failed': #it has been pushed up
				# 	print("this one has been resubmitted. looks like we already pushed it.")
				# 	# print(title)
				# 	print("so we will have to update this fsattempt")
					
				# 	already_subbed = True
				# 	break
				# elif old_fsAttempt.status=='ready-for-push': #it has not yet been pushed.
				# 	# change the old one to failed status
				# 	# print("this one has been resubmitted and we did NOT push to figshare.")
				# 	old_fsAttempt.status='failed'
				# 	# print(title)
				# 	# print(old_attempt.oama_fk.message_id)
				# 	old_fsAttempt.note+='\nthis is a resubmission. the last one was not pushed to fs. the new oas id: '+str(mj['id'])
				# 	old_fsAttempt.save()
				# 	#continue on
				# 	continue
				##############old code above
				message_to_fs['status']="update"
				#can i do this  ? NO I CAN'T. 
				# old_fsAttempt(fs_attempt_json=json.dumps(message_to_fs), oama_fk=message)
				# old_fsAttempt.save()
				fsa = fsAttempt(fs_attempt_json=json.dumps(message_to_fs), oama_fk=message)
				fsa.note+='\nwe gotta update this badboy but not right now. work this out in... the future. good luck.'
			else: # no dups. so go ahead and save.
				fsa = fsAttempt(fs_attempt_json=json.dumps(message_to_fs), oama_fk=message)
			if already_subbed:
				fsa.status="failed"
				fsa.note+='\nthere was a resubmission with oas id '+str(mj['id'])
			fsa.save()
			#save this attempt with the authors.
			for author in article_orcid_authors:
				author.articles.add(fsa)
				author.save()

	def handle(self, *args, **options):

		self.convert_oa()

