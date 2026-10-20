from django.core.management.base import BaseCommand
from transfer.models import oaMessage,fsAttempt,repoLicense
from transfer.utils import get_val, handle_mess, check_orcid_user_in_fs
from transfer.settings import in_copyright_num, figshare_group_id
import json, re
from datetime import datetime



class Command(BaseCommand):
	# for matching orcid :)
	orcid_match = re.compile("\d{4}-\d{4}-\d{4}-(\d{3}X|\d{4})")

	def convert_oa(self):
		# get messages resady to be converted to figshare.
		ready_messages = oaMessage.objects.filter(status='oa-ready')#get the ready oa-messages
		message_counter=0
		
		# iterate, reading the json and then finding necessary/relevant variables.
		for message in ready_messages:
			already_subbed = False
			message_counter+=1

			# analyze the message json. get essential vars and create the fsAttempt object.
			mj = json.loads(message.json)
			article = mj['data']['article']
			title = article['title']
			new_doi = article['doi'][16:len(article['doi'])]
			# json.loads(i.json)['doi']
			message_to_fs = {"authors":[],"funding_list":[],"title":title,"published_date":"","status":"published","license":0,"doi":new_doi,"keywords":['OA Switchboard'],"defined_type":"journal contribution","group_id":figshare_group_id}

			
			
			# add description
			message_to_fs['description'] = "This journal contribution is published Open Access by the publisher. Follow the DOI link to retrieve a copy of the full text.\n" + get_val(article,'acknowledgement')
			
			
			# authors
			authors = mj['data']['authors']
			
			for this_guy in authors:
				# example:
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
				fn = get_val(this_guy,'firstName')
				ln = get_val(this_guy,'lastName')
				# ini = get_val(this_guy,'initials')
				orcid = str(get_val(this_guy,'ORCID'))
				fs_user = 0
				author_dict = {}

				if orcid == "":
					message = handle_mess("issue","\ncouldn't find orcid id for "+ fn + " " + ln,message)
				elif "orcid.org" in orcid: # if orcid dot org is in the thing
					orcid = orcid.split('/')[3] #split the url and get the last part which is the orcid id to see if it's valid
					if self.orcid_match.match(orcid) is None or len(orcid.split('-'))>4:
						orcid=""
						message = handle_mess("issue","\ncouldn't find or improperly formatted orcid id for "+ fn + " " + ln,message)
					else:# there is a legit orcid id check if the user is in figshare.
						fs_user = check_orcid_user_in_fs(orcid)
						if fs_user != 0:
							author_dict = fs_user
				# it may have been submitted not as blank and not with doi.org. so assume 0000-0000-0000-0000.
				elif self.orcid_match.match(orcid) is None or len(orcid.split('-'))>4:# it's not valid.
					orcid=""
					message = handle_mess("issue","\ncouldn't find or improperly formatted orcid id for "+ fn + " " + ln,message)
				else: # alright lets assume its good.
					fs_user = check_orcid_user_in_fs(orcid)
					if fs_user != 0:
						author_dict = fs_user
				
				if len(author_dict)==0: #if we didn't find a user in figshare with this orcid, then just add the name and orcid to the authors list.	
					author_dict = {"name":fn+" "+ln,"first_name":fn,"last_name":ln,"orcid_id":orcid}						
				
				message_to_fs['authors'].append(author_dict)


			
			# publication date.
			publication_date = ""
			if get_val(article,'manuscript'):# if there's manuscript
				if get_val(article['manuscript']['dates'],'publication'):
					publication_date = article['manuscript']['dates']['publication']
					message_to_fs['published_date'] = publication_date
				elif get_val(article['manuscript']['dates'],'acceptance'):
					publication_date = article['manuscript']['dates']['acceptance']
					message_to_fs['published_date'] = publication_date
				elif publication_date == "":
					message = handle_mess("error", "theres no clear publication date", message)
					fsAttempt(json=json.dumps(message_to_fs), doi=new_doi, oam_fk=message).save()
					#can't go further without publication date.
					continue
			else:
				message = handle_mess("error", "theres no manuscript section in message", message)
				fsAttempt(json=json.dumps(message_to_fs), doi=new_doi, oam_fk=message).save()
				#can't go further without manuscript date.
				continue

			
			
			# get license.
			license = repoLicense.objects.filter(name=article['vor']['license'])
			if not license:
				# no matching license. use the default in_copyright_num
				message_to_fs['license']= in_copyright_num
				message = handle_mess("issue", "using default license. there is no matching license. was looking for: " + article['vor']['license'], message)
				# print("\nthere's no matching license here!!!!\n")
			else:
				# confident in using [0] here because of unique constraint on the model
				message_to_fs['license']=int(license[0].value)

			
			
			
			#grant info.
			if len(get_val(article,'grants'))>0:

				for grant in article['grants']:
					# print(grant)
					if len(get_val(grant,'name'))>0:
						message_to_fs['funding_list'].append({"grant_code":grant['name']})
					elif len(get_val(grant,'id'))>0:
						message_to_fs['funding_list'].append({"grant_code":grant['id']})
					else:
						message_to_fs['funding_list'].append({"grant_code":0})
						message = handle_mess("issue", "could not determine grant code", message)

			
			
			# checking if this is a resubmission.
			if get_val(mj['header']['meta'],'resubmitted'):
				print(" its resubmitted.")
				# this is a resubmission. did we already upload it?
				# get the old attempt
				old_fsAttempt = fsAttempt.objects.filter(doi=new_doi)
				if len(old_fsAttempt)>0:
					print("we will have to update this. gotta put in some addt code to handle this.")
					#change old_fsAttempt status to update
					old_fsAttempt.update(status='updated')
					old_fsAttempt = old_fsAttempt.first()
					#get the figshare entry id and add it to the current fsAttempt
					message_to_fs['fs_id']=old_fsAttempt.fs_id
					#this is a resubmission. we will have to update the old one.
					message = handle_mess("update", "this is a resubmission. we will have to update the old one.", message)
					# so search in a diff file for messages with status "update" and an fs_id.
			
			
			if get_val(message_to_fs,'fs_id') != 0:#check if there is an fs_id in message_to_fs. if there is then this is an update
				message_to_fs['status']='ready-for-push' #otherwise it's ready to push.
			else:
				message_to_fs['status']='update' #otherwise it's ready to push.
			fsa = fsAttempt(json=json.dumps(message_to_fs), doi=new_doi, oam_fk=message)
			fsa.save()
	def handle(self, *args, **options):

		self.convert_oa()

