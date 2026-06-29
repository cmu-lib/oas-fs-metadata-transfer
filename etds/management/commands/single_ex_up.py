from time import sleep

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from etds.models import pqAttempt,pqFsAttempt,fsToken
from oafs.settings import BASE_DIR
import json
import os
import re
import requests
import xmltodict
from pathlib import Path
import datetime
from zipfile import ZipFile
from requests.exceptions import HTTPError
import hashlib
import csv
import shutil
from django.core.mail import send_mail

class Command(BaseCommand):

	# set vars
	BASE_DIR = Path(__file__).resolve().parent
	ziplist = os.listdir(str(BASE_DIR)+'/../../zippies')
	p = "DISS_" #idk why pq wants to use this as a prefix for literally every field
	working_files_location =str(BASE_DIR)+"/working/"
	CHUNK_SIZE = 1048576
	fs_base_url=""
	upload_files = []
	token = ""
	
	# secret vars 
	# this should be using the settings file. like: oafs.settings.fs_base_url 

	with open(str(BASE_DIR)+'/../../../pq_secrets.json') as f:
		secrets = json.loads(f.read())
	if secrets['is_dev']:
		fs_base_url= "https://api.figsh.com/v2/"
		in_copyright = 44
		group_id = secrets["figshare_group_id_dev"]
		figshare_client_id = secrets["figshare_client_id_dev"]
		figshare_client_secret = secrets["figshare_client_secret_dev"]
		figshare_user = secrets["figshare_user_dev"]
		license = secrets["in_copyright_dev"]
	else:
		fs_base_url= "https://api.figshare.com/v2/"
		in_copyright = 43
		group_id = secrets["figshare_group_id_prod"]
		figshare_client_id = secrets["figshare_client_id_prod"]
		figshare_client_secret = secrets["figshare_client_secret_prod"]
		figshare_user = secrets["figshare_user_prod"]
		license = secrets["in_copyright_prod"]
	
	# vars from pqkh degree csv
	degree_map = []
	with open(str(BASE_DIR)+'/../../pqkh_degree_map.csv') as f:
		# degree_map = {row[0]:row[1] for row in csv.reader(f, delimiter='\t')}
		reader = csv.reader(f, delimiter='\t')
		degree_map = list(reader)
	# print(degree_map)
	# exit()
	#ex:
	#[...['Tepper', "Master's Thesis", '', 'Master of Business Administration', 'M.A.'], 
	# ['Tepper', "Master's Thesis", '', 'Master of Innovation Product Development', 'M.I.I.P.S']]
	department_categories = []
	department_ids = []
	with open('etds/subjects/ANZSRC.csv', newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter='\t')
		for row in reader:
			department_categories.append(row[1])  # 0 for the first column of
			department_ids.append(int(row[0]))  # 0 for the first column of

	# func to convert xml to json dict
	def xml_to_json(self,file):
		with open(file) as xml_file:
			# make a dict
			return xmltodict.parse(xml_file.read())[self.p+'submission']

	def handle_failures(self,e,msg="no message",title="no title",send_email=False):
		print("There was an error:", e)
		print("Error message:", msg)
		print("Thesis title:", title)
		if send_email:
			send_mail(
					subject='PQ->FS Manual review: '+title,
					message= msg,
					from_email='penelopecruz@ok',
					recipient_list=['kiritharan@cmu.edu'],
					fail_silently=False,
				)
		
		self.upload_files = []
		# Here you could add logging or email notification

	### the following functions are from the example upload on figshare docs https://docs.figshare.com/#example-upload ###
	def raw_issue_request(self,method, url, data=None, binary=False):
		headers = {'Authorization': 'token ' + self.is_token()}
		if data is not None and not binary:
			data = json.dumps(data)
		response = requests.request(method, url, headers=headers, data=data)
		try:
			response.raise_for_status()
			try:
				data = json.loads(response.content)
			except ValueError:
				data = response.content
		except HTTPError as error:
			print('HTTP error occurred: {}'.format(error))
			# print('Caught an HTTPError: {}'.format(error.message))
			print('Body:\n', response.content)
			raise

		return data

	def issue_request(self, method, endpoint, *args, **kwargs):
		return self.raw_issue_request(method, self.fs_base_url+endpoint, *args, **kwargs)

	def upload_parts(self, file_info,file_location):
		url = '{upload_url}'.format(**file_info)
		result = self.raw_issue_request('GET', url)

		print('Uploading parts:')
		with open(file_location, 'rb') as fin:
			for part in result['parts']:
				self.upload_part(file_info, fin, part)
		print

	def upload_part(self, file_info, stream, part):
		udata = file_info.copy()
		udata.update(part)
		url = '{upload_url}/{partNo}'.format(**udata)

		stream.seek(part['startOffset'])
		data = stream.read(part['endOffset'] - part['startOffset'] + 1)

		self.raw_issue_request('PUT', url, data=data, binary=True)
		print('  Uploaded part {partNo} from {startOffset} to {endOffset}'.format(**part))
	def get_file_check_data(self, file_name):
		with open(file_name, 'rb') as fin:
			md5 = hashlib.md5()
			size = 0
			data = fin.read(self.CHUNK_SIZE)
			while data:
				size += len(data)
				md5.update(data)
				data = fin.read(self.CHUNK_SIZE)
			return md5.hexdigest(), size

	def initiate_new_upload(self, article_id, file_name):
		endpoint = 'account/articles/{}/files'
		endpoint = endpoint.format(article_id)

		md5, size = self.get_file_check_data(file_name)
		data = {'name': os.path.basename(file_name),
				'md5': md5,
				'size': size}

		result = self.issue_request('POST', endpoint, data=data)
		print('Initiated file upload:', result['location'], '\n')

		result = self.raw_issue_request('GET', result['location'])

		return result

	### end this block from FS ###

	def get_token(self,t=None):
		headers = {
				'Content-Type': 'application/json',
				}

		json_data = {
		'client_id': self.figshare_client_id,
		'client_secret': self.figshare_client_secret,
		'grant_type': 'client_credentials',
		}

		fs_token_response = requests.post(self.fs_base_url+'token', headers=headers, json=json_data).json()
		print(json.dumps(fs_token_response))
		
		token = fs_token_response['token']
		t = fsToken.objects.update_or_create(pk=1, defaults={'token': token, 'created': timezone.now()})[0]
		t.token = token
		t.created = timezone.now()
		t.save()
		return(t)

	def is_token(self):
		# token_file = open('fs_token.txt','r')
		try:
			token = fsToken.objects.get(pk=1)  
			token_time = datetime.datetime.fromisoformat(str(token.created))
			
			if (timezone.now() - token_time).total_seconds() < 3500: #tokens last an hour, so if it's been less than 3500 seconds just use it.
				return(token.token)
			else:
				print('token expired, getting new one') 
				return self.get_token().token
		except fsToken.DoesNotExist:
			# Handle the case where the object is not found
			print("need a new token")
			return self.get_token().token

	# used for authors and advisors. 
	def process_name(self,author,is_author=True,fs_author_id=0):
		name = author[self.p+'name'][self.p+'fname']+" "+str('' if author[self.p+'name'][self.p+'middle'] is None else author[self.p+'name'][self.p+'middle']+ " ") + author[self.p+'name'][self.p+'surname']
		first_name = author[self.p+"name"][self.p+'fname']
		last_name = author[self.p+"name"][self.p+'surname']
		if is_author and author[self.p+"orcid"] is not None:
			orcid_id = author[self.p+"orcid"]
			# return{"name": "", "last_name": "", "orcid_id":orcid_id}
			print("yeah we have orcid")
			headers = {
				'Content-Type': 'application/json',
			}
			params = {
				'access_token': self.is_token(),
			}
			response = requests.post(self.fs_base_url+'account/authors/search', params=params, headers=headers, data='{"orcid":"'+orcid_id+'"}').json()
			print(response)
			if len(response) >0:
				print('ok response')
				return {'id': response[0]['id']}
			# exit()
			# return {"id":4614126}
			else:
				print("this must be a new person")
				return{"name":name,"first_name":first_name,"last_name":last_name,"orcid_id":orcid_id}		
		else:
			orcid_id = ""
		return{"name":name,"first_name":first_name,"last_name":last_name,"orcid_id":orcid_id}


	# main work of converting fields from proquest dict to figshare dict
	def convert_pq_to_fs(self,data_dict,pqfs=None):
		figshare_json = {'authors':[],'keywords':[],"defined_type":"thesis","group_id":self.group_id}
		# authors first
		authors_data = data_dict[self.p+'authorship']
		if isinstance(authors_data,list):
			for x in authors_data:
				figshare_json['authors'].append(self.process_name(x[self.p+'author']))
		else:
			# print(authors_data)
			figshare_json['authors'].append(self.process_name(authors_data[self.p+'author']))

		#basic info like title, abstract, date
		title = data_dict[self.p+"description"][self.p+'title']
		# print(title)
		published_date = data_dict[self.p+"description"][self.p+'dates'][self.p+'accept_date']
		published_date= datetime.datetime.strptime(published_date, "%d/%m/%Y").strftime("%Y-%m-%d")
		# print(published_date)
		# exit()

		advisors_data = data_dict[self.p+"description"][self.p+"advisor"]
		advisors_str = ""
		advisors_loop_first = True
		if isinstance(advisors_data,list):
			for x in advisors_data:
				if advisors_loop_first:
					advisors_str += self.process_name(x,False)['name']
					advisors_loop_first = False
				else:
					advisors_str += ", " + self.process_name(x,False)['name']
		else:
			# print(authors_data)
			#assuming when it's solo there's a p+advisor in this key like there is for author
			advisors_str += self.process_name(advisors_data,False)['name']

			# figshare_json['advisors'].append(self.process_name(advisors_data[self.p+'advisor'],False))


		#content
		if isinstance(data_dict[self.p+"content"][self.p+'abstract'][self.p+'para'],list):
			description = ' '.join(data_dict[self.p+"content"][self.p+'abstract'][self.p+'para'])
		else:
			description = data_dict[self.p+"content"][self.p+'abstract'][self.p+'para']#[0:1999]

		#embargo
		if data_dict["@embargo_code"] != "0":
			figshare_json['is_embargoed'] = True
			embargo_date = datetime.datetime.strptime(data_dict[self.p+'restriction'][self.p+'sales_restriction']['@remove'], "%m/%d/%Y").strftime("%Y-%m-%d")
			figshare_json['embargo_date'] = embargo_date
			figshare_json['embargo_type'] = "file"
		else:
			figshare_json['is_embargoed'] = False
			figshare_json['embargo_date'] = None
			figshare_json['embargo_type'] = None

		#add together...
		figshare_json['description']=description
		figshare_json['title']=title
		figshare_json['license']=self.license 
		figshare_json['published_date']=published_date
		print(data_dict[self.p+"description"][self.p+'degree'])
		degree_name = ""
		degree_type = ""
		if data_dict[self.p+"description"][self.p+'degree'] == "Ph.D." or data_dict[self.p+"description"][self.p+'degree'] == "Ph.D":
			degree_type = "Dissertation"
			degree_name = "Doctor of Philosophy (PhD)"
		elif data_dict[self.p+"description"][self.p+'degree'] == "M.A." or data_dict[self.p+"description"][self.p+'degree'] == "M.A":
			degree_type = "Master's Thesis"
			degree_name = "Master of Arts (MA)"
		else:
			for degree in self.degree_map:
				print(degree)
				if degree[4] == data_dict[self.p+"description"][self.p+'degree']:
					degree_type = degree[1]
					degree_name = degree[2]
					if degree_type == "":
						self.handle_failures(e="Degree TYPE not in options. Manual review needed.",msg="Degree type not in options: "+data_dict[self.p+"description"][self.p+'degree']+". ",title=title,send_email=True)
						pqfs.note += "Degree type not in options: "+data_dict[self.p+"description"][self.p+'degree']+". "
						pqfs.save()
					if degree_name == "":
						self.handle_failures(e="Degree NAME not in options. Manual review needed.",msg="Degree name not in options: "+data_dict[self.p+"description"][self.p+'degree']+". ",title=title,send_email=True)
						pqfs.note += "Degree name not in options: "+data_dict[self.p+"description"][self.p+'degree']+". "
						pqfs.save() 
					break
		# can't find a degree at all.
		if degree_type == "" or degree_name == "":
			self.handle_failures(e="Degree type not in options. Manual review needed.",msg="Degree type not in options: "+data_dict[self.p+"description"][self.p+'degree']+". ",title=title,send_email=True)
			pqfs.note += "Degree type not in options: "+data_dict[self.p+"description"][self.p+'degree']+". "
			pqfs.save()
			# break
		
		# department name here.
		dept_name = data_dict[self.p+"description"][self.p+'institution'][self.p+"inst_contact"]

		# keywords
		figshare_json['keywords']+=re.split(r',\s*',data_dict[self.p+"description"][self.p+'categorization'][self.p+'keyword']) if data_dict[self.p+"description"][self.p+'categorization'][self.p+'keyword'] is not None else []
		
		#cats
		cat_desc = data_dict[self.p+"description"][self.p+'categorization'][self.p+'category']
		categories = [] 

		if isinstance(cat_desc,list):
			# [{'DISS_cat_code': '0548', 'DISS_cat_desc': 'Mechanical engineering'}, {'DISS_cat_code': '0794', 'DISS_cat_desc': 'Materials Science'}, {'DISS_cat_code': '0771', 'DISS_cat_desc': 'Robotics'}]
			for cat in cat_desc:
				figshare_json['keywords'].append(cat[self.p+'cat_desc'])
				if cat[self.p+'cat_desc'] in self.department_categories:
					#figshare can't add these categories so just shove them in keywords
					# i forget exactly why but i think the codes don't match up... between pq and kh 
					# so i'll just keep it empty but this is how you would:
					# idx = self.department_categories.index(cat[self.p+'cat_desc'])
					# categories.append(self.department_ids[idx])
					figshare_json['keywords'].append(cat[self.p+'cat_desc'])
				else:
					# not in options and cannot add on fs so no need to note this.
					# add this cat into keywords
					figshare_json['keywords'].append(cat[self.p+'cat_desc'])
					

		elif isinstance(cat_desc,dict):

			if cat_desc[self.p+'cat_desc'] in self.department_categories:
				# categories.append(int(cat_desc[self.p+'cat_code']))
				# idx = self.department_categories.index(cat[self.p+'cat_desc'])
				# categories.append(self.department_ids[idx])
				figshare_json['keywords'].append(cat_desc[self.p+'cat_desc'])
			else:
				figshare_json['keywords'].append(cat_desc[self.p+'cat_desc'])

		figshare_json['categories'] = categories #this is just empty.

		#custom fields here.
		figshare_json['custom_fields_list']=[
			{'name':"Advisor(s)","value":advisors_str},
			{'name':'Degree Type', 'value':[degree_type]},
			{'name':'Degree Name', 'value':[degree_name]},
			{'name':"Date","value":datetime.datetime.today().strftime('%Y-%m-%d')}, 
			{'name':'Thesis Department','value':[dept_name]}
		]

		return(figshare_json)

	def rm_user_and_add_files(self,article_id,upload_files,figshare_json,pqfs): # figshare automatically adds myself as a user to articles. 
		headers = {
			'Content-Type': 'application/json',
		}
		params = {
			'access_token': self.is_token(),
		}
		# delete the user 
		response = requests.delete(self.fs_base_url+"account/articles/"+str(article_id)+"/authors/"+self.figshare_user,params=params,headers=headers)
		print(response.__dict__)
		pqfs.status = 'removed-user'
		print("removed user, now adding file")
		pqfs.save()
		# update embargo info
		if figshare_json['is_embargoed']:
			response = requests.put(self.fs_base_url+"account/articles/"+str(article_id)+"/embargo",params=params,headers=headers,data=json.dumps({'is_embargoed':figshare_json['is_embargoed'],'embargo_date':figshare_json['embargo_date'],'embargo_type':figshare_json['embargo_type']}))
			pqfs.status = 'updated-embargo'
			pqfs.save()
		# return()
		# Then we upload the file(s).
		for file_location in upload_files:
			print(file_location)
			if os.path.isdir(file_location):
				print("ok this is a folder!")
				continue # skip the supplemental folder itself.
			if ".xml" in file_location:
				continue # skip the xml file itself. 
				
			file_info = self.initiate_new_upload(article_id, file_location)
			# Until here we used the figshare API; following lines use the figshare upload service API.
			self.upload_parts(file_info,file_location)
			pqfs.status = 'uploading: ' + file_location
			pqfs.save()
			# We return to the figshare API to complete the file upload process.
			self.issue_request('POST', 'account/articles/{}/files/{}'.format(article_id, file_info['id']))
		pqfs.status = 'success'
		pqfs.save()


	#LET'S F%(*ING GO
	def add_arguments(self , parser):
		parser.add_argument('--zip', action='append', type=str, help='specific zip file to upload. can be used multiple times for multiple zips.')

	def handle(self, *args, **options):
		if options['zip'] is not None:
			for z_thesis in options['zip']:	
				
				print('working on '+z_thesis)# this should be the name of the zip file in the zippies folder.
				# exit()
				data_dict = {}
				# check if there are files first
				are_there_files = os.listdir(self.working_files_location)
				if len(are_there_files)>0: # if there are then kill them
					for f in are_there_files:
						fp = os.path.join(self.working_files_location, f)
						try:
							if os.path.isfile(fp) or os.path.islink(fp):
								os.remove(fp)
							elif os.path.isdir(fp):
								shutil.rmtree(fp)
						except Exception as e:
							print('failed to delete ' + fp + '. reason: ' + str(e))

				# loading the temp.zip and creating a zip object
				with ZipFile(str(BASE_DIR)+'/etds/zippies/'+z_thesis, 'r') as z_t:
					# Extracting all the members of the zip
					# into a specific location.
					z_t.extractall(
						path=self.working_files_location
					)

				the_files = os.listdir(self.working_files_location)
				print(the_files)
				print("these are the files in the zip")
				supplemental_files = []
				for f in the_files:
					print(f)
					if '.xml' in f:
						print("we have the fxml clearly")
						xml_file = self.working_files_location+f
						data_dict= self.xml_to_json(xml_file)
					elif os.path.isdir(self.working_files_location+f):
						self.upload_files.append(self.working_files_location+f) 
						print("found a directory")
						files_in_submitted_folder = os.listdir(self.working_files_location+f)
						
						for sf in files_in_submitted_folder:
							print(sf)
							self.upload_files.append(self.working_files_location+f+"/"+sf)
							# move these files to the working directory so we can upload them to figshare and then delete them. 
							# shutil.move(self.working_files_location+f+"/"+sf,self.working_files_location+sf)
							# add the moved file to the list of files in the zip for record keeping in the pqAttempt model.
							# the_files.append(self.working_files_location+f+"/"+sf)

					else:
						#probably the pdf. we will upload this to figshare and then delete it. so save the location for now.
						self.upload_files.append(self.working_files_location+f)
				# all these files are now in the working folder. 
				# save the original pq json for debugging 
				print(self.upload_files)
				# exit()
				print(data_dict)
				print("here is the dict dick")
				pqa = pqAttempt()
				pqa.title = data_dict[self.p+"description"][self.p+'title']
				pqa.zip_title = z_thesis
				pqa.pq_id = data_dict[self.p+'description'][self.p+'identifiers']['pubNumber']
				pqa.pq_json = json.dumps(data_dict,indent=4)
				pqa.status = 'attempting-convert'
				pqa.other_files = [f+"\n" for f in the_files if f != os.path.basename(xml_file)]
				pqa.save()
				pqfs = pqFsAttempt()
				pqfs.pqa_fk = pqa
				pqfs.status = 'attempting-convert'
				pqfs.save()
				figshare_json = self.convert_pq_to_fs(data_dict,pqfs)
				print(figshare_json)
				# save converted json in case there's an issue downstream
				
				pqfs.fs_attempt_json = json.dumps(figshare_json,indent=4)
				pqfs.status = 'attempting-push'
				pqfs.save()

				pqa.status = "converted-to-fsjson"
				pqa.save()

				# token and push attempt
				fs_token = self.is_token()
				print(fs_token)
				headers = {
							'Content-Type': 'application/json',
				}
				params = {
					'access_token': fs_token,
				}
				response = requests.post(self.fs_base_url+'account/articles', params=params, headers=headers, data=json.dumps(figshare_json)).json()
				print(response)
				

				#cleanup
				try: # this should be expanded. there are many other places this can fail. hhhhhhhhhhh
					article_id = response['entity_id']
					pqfs.fs_id = article_id
					pqfs.save()
					print("cool article went through")
					self.rm_user_and_add_files(article_id,self.upload_files,figshare_json,pqfs)
					if len(self.upload_files)>1:
						for sf in supplemental_files: #remove the supplemental files
							if os.path.isdir(sf):
								shutil.rmtree(sf)
							else:
								os.remove(sf)
					os.remove(xml_file)
					self.upload_files = []
				except KeyError:
					print('NO ARTICLE WAS SAVED OMG')
					print(response['code'])
					rcode = "Article was not created on figshare. Response code: "+str(response['code'])+". "+str(response['message'])
					# here we should send an email and debug but continue
					# if "There can't be 2 users having the same orcid" in str(response['message']):
					# we run it again with just orcid.
					pqfs.response = str(response)
					pqfs.status = "failed-at-push"
					pqfs.note += rcode
					pqfs.save()
					self.handle_failures(e=str(response['code'])+" . "+str(response['message']),msg=rcode,title=data_dict[self.p+"description"][self.p+'title'],send_email=True)
					
					pass
