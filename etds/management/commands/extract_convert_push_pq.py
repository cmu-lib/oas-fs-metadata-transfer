from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from etds.models import pqAttempt,pqFsAttempt,fsToken
from oafs.settings import secrets,BASE_DIR,fs_base_url
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

class Command(BaseCommand):

	# set some vars to be used 
	# BASE_DIR = Path(__file__).resolve().parent
	p = "DISS_" #idk why pq wants to use this as a prefix for literally everything... WE GET IT
	file_location ="zippies/working/"
	CHUNK_SIZE = 1048576

	# list of categories from ANZSRC https://www.abs.gov.au/statistics/people/education/anzsco-australian-and-new-zealand-standard-classification-occupations/latest-release#data-downloads
	# which is what figshare respects. 
	department_categories = []
	department_ids = []
	with open('etds/subjects/ANZSRC.csv', newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter='\t')
		for row in reader:
			department_categories.append(row[1])  # 0 for the first column of
			department_ids.append(int(row[0]))  # 0 for the first column of
	# department_categories = ["Architecture","Art","Biological Sciences","Biomedical Engineering","Center for the Neural Basis of Cognition","Chemical Engineering","Chemistry","Civil and Environmental Engineering","Computer Science","Design","Economics","Electrical and Computer Engineering","Engineering and Public Policy","English","History","Human-Computer Interaction Institute","Information Networking Institute","Information Systems and Management","Institute for Software Research","Language Technologies Institute","Machine Learning","Materials Science and Engineering","Mathematical Sciences","Mechanical Engineering"]
	department_degree_name = ["Doctor of Philosophy (PhD)", "Master of Architecture (MArch)", "Master of Arts (MA)", "Master of Arts Management (MAM)", "Master of Design (MDes)", "Master of Entertainment Technology (MET)", "Master of Information Systems Management (MISM)", "Master of Product Development (MPD)", "Master of Science (MS)", "Master of Science in Chemical Engineering (MSChE)", "Master of Science in Information Security Policy and Management (MSISPM)", "Master of Science in Information Technology (MSIT)", "Master of Science in Public Policy and Management (MSPPM)", "Master of Science in Sustainable Design (MSSD)", "Master of Urban Planning (MUP)", "Master of Statistical Practice (MSP)", "Master of Fine Arts (MFA)"]
	degree_type_dev = ["Master's Thesis","Dissertation","Ph.D."]

	# secret vars 
	with open(str(BASE_DIR)+'/secrets.json') as f:
		secrets = json.loads(f.read())
	ziplist = os.listdir(str(BASE_DIR)+'/etds/zippies')

	# ^^ main vars.



	# func to convert xml to json dict
	def xml_to_json(self,file):
		with open(file) as xml_file:
			# make a dict
			return xmltodict.parse(xml_file.read())[self.p+'submission']

	def handle_failures(self,e):
		print("There was an error:", e)
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
			print('Caught an HTTPError: {}'.format(error.message))
			print('Body:\n', response.content)
			raise

		return data

	def issue_request(self, method, endpoint, *args, **kwargs):
		return self.raw_issue_request(method, fs_base_url+endpoint, *args, **kwargs)

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
		'client_id': secrets['figshare_client_id'],
		'client_secret': secrets['figshare_client_secret'],
		'grant_type': 'client_credentials',
		}

		fs_token_response = requests.post(fs_base_url+'token', headers=headers, json=json_data).json()
		print(json.dumps(fs_token_response))
		
		token = fs_token_response['token']
		# t = fsToken.objects.get(pk=1)
		t.token = token
		t.created = timezone.now()
		t.save()
		return(t)

	def is_token(self):
		# token_file = open('fs_token.txt','r')
		try:
			token = fsToken.objects.get(pk=1)  
			# token_time = datetime.datetime.fromisoformat(token.created.isoformat())
			
			# print(token.created)
			# 2024-08-20 00:00:00+00:00
			# dt_naive = datetime.datetime.strptime(str(token.created), "%Y-%m-%d %H:%M:%S%z")


			token_time = datetime.datetime.fromisoformat(str(token.created))
			# print(token_time)
			# print(timezone.now())
			# print((timezone.now() - token_time).total_seconds())
			# exit()
			if (timezone.now() - token_time).total_seconds() < 3500: #tokens last an hour, so if it's been less than 3500 seconds just use it.
				return(token.token)
			else:
				print('token expired, getting new one') 
				return self.get_token(token).token
		except fsToken.DoesNotExist:
			# Handle the case where the object is not found
			print("need a new token")
			return self.get_token(token).token

	# used for authors and advisors. 
	def process_name(self,author,is_author=True):
		name = author[self.p+'name'][self.p+'fname']+" "+str('' if author[self.p+'name'][self.p+'middle'] is None else author[self.p+'name'][self.p+'middle'])+ " " +author[self.p+'name'][self.p+'surname']
		first_name = author[self.p+"name"][self.p+'fname']
		last_name = author[self.p+"name"][self.p+'surname']
		if is_author:
			orcid_id = author[self.p+"orcid"]
		else:
			orcid_id = ""
		return{"name":name,"first_name":first_name,"last_name":last_name,"orcid_id":orcid_id}


	# main work of converting fields from proquest dict to figshare dict
	def convert_pq_to_fs(self,data_dict,pqfs=None):
		figshare_json = {'authors':[],'keywords':[],"defined_type":"thesis","group_id":secrets["figshare_group_id_dev"]}
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
		figshare_json['license']=44 #"in copyright" ! make sure you change this to 43 in prod
		figshare_json['published_date']=published_date

		# check if these custom fileds exist or whatever.
		if data_dict[self.p+"description"][self.p+'degree'] not in self.degree_type_dev:
			pqfs.note += "Degree type not in options: "+data_dict[self.p+"description"][self.p+'degree']+". "
			
			degree_type = ""
		else:
			degree_type = data_dict[self.p+"description"][self.p+'degree']

		# department name here.
		dept_name = data_dict[self.p+"description"][self.p+'institution'][self.p+"inst_contact"]
		# print(dept_name)
		if dept_name not in self.department_degree_name:
			pqfs.note += "department name in options: "+dept_name+". "
			pqfs.save() # alert to this because we should be able to add more department names to fs.


		# keywords
		figshare_json['keywords']+=re.split(r',\s*',data_dict[self.p+"description"][self.p+'categorization'][self.p+'keyword']) if data_dict[self.p+"description"][self.p+'categorization'][self.p+'keyword'] is not None else []
		#pretty slick, no?
		
		#cats
		first_cat_loop = True
		cat_desc = data_dict[self.p+"description"][self.p+'categorization'][self.p+'category']
		categories = []

		if isinstance(cat_desc,list):
			# [{'DISS_cat_code': '0548', 'DISS_cat_desc': 'Mechanical engineering'}, {'DISS_cat_code': '0794', 'DISS_cat_desc': 'Materials Science'}, {'DISS_cat_code': '0771', 'DISS_cat_desc': 'Robotics'}]
			for cat in cat_desc:
				if cat[self.p+'cat_desc'] in self.department_categories:
					#figshare sucks and can't add these categories so just shove them in keywords
					#should they fix it then uncomment the next two
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

		figshare_json['categories'] = categories

		#custom fields here.
		figshare_json['custom_fields_list']=[
			{'name':"Advisor(s)","value":advisors_str},
			{'name':'Degree Type', 'value':[degree_type]},
			{'name':"Date","value":datetime.datetime.today().strftime('%Y-%m-%d')}, 
			{'name':'Department','value':[dept_name]}
		]
		print(figshare_json)
		return(figshare_json)

	def rm_user_and_add_file(self,article_id,file_location,figshare_json,pqfs): # figshare automatically adds myself as a user to articles. 
		headers = {
			'Content-Type': 'application/json',
		}
		params = {
			'access_token': self.is_token(),
		}
		# delete the user 
		response = requests.delete(fs_base_url+"account/articles/"+str(article_id)+"/authors/"+secrets['figshare_user'],params=params,headers=headers)
		pqfs.status = 'removed-user'
		pqfs.save()
		# update embargo info
		if figshare_json['is_embargoed']:
			response = requests.put(fs_base_url+"account/articles/"+str(article_id)+"/embargo",params=params,headers=headers,data=json.dumps({'is_embargoed':figshare_json['is_embargoed'],'embargo_date':figshare_json['embargo_date'],'embargo_type':figshare_json['embargo_type']}))
			pqfs.status = 'updated-embargo'
			pqfs.save()
		# return()
		# Then we upload the file.
		file_info = self.initiate_new_upload(article_id, file_location)
		# Until here we used the figshare API; following lines use the figshare upload service API.
		self.upload_parts(file_info,file_location)
		# We return to the figshare API to complete the file upload process.
		self.issue_request('POST', 'account/articles/{}/files/{}'.format(article_id, file_info['id']))
		pqfs.status = 'success'
		pqfs.save()


	#LET'S F%(*ING GO
	def handle(self, *args, **options):
		zt = pqAttempt.objects.all().values_list('zip_title', flat=True)
		for z_thesis in self.ziplist:
			if '.zip' not in z_thesis: # its not a zip.
				continue
			if z_thesis in zt:
				print(z_thesis+" has already been attempted. skipping.")
				continue
			print('working on '+z_thesis)
			data_dict = {}
			# check if there are files first
			are_there_files = os.listdir(str(BASE_DIR)+'/etds/working')
			if len(are_there_files)>0: # if there are then kill them
				for f in are_there_files:
					os.remove(str(BASE_DIR)+'/etds/working/'+f)
			# loading the temp.zip and creating a zip object

			with ZipFile(str(BASE_DIR)+'/etds/zippies/'+z_thesis, 'r') as z_t:

				# Extracting all the members of the zip
				# into a specific location.
				z_t.extractall(
					path=str(BASE_DIR)+'/etds/working')
			the_files = os.listdir(str(BASE_DIR)+'/etds/working')
			a_file = the_files[0].split('.')
			if a_file[1]=='pdf':
				# this is pdf use the other file (1)
				xml_file = str(BASE_DIR)+'/etds/working/'+the_files[1]
				data_dict= self.xml_to_json(xml_file)
				upload_file = str(BASE_DIR)+'/etds/working/'+the_files[0]
			else:
				xml_file = str(BASE_DIR)+'/etds/working/'+the_files[0]
				data_dict= self.xml_to_json(xml_file)
				upload_file = str(BASE_DIR)+'/etds/working/'+the_files[1]
			# token and push attempt
			fs_token = self.is_token()

			headers = {
						'Content-Type': 'application/json',
			}
			params = {
				'access_token': fs_token,
			}
			# save the original pq json for debugging 

			pqa = pqAttempt()
			pqa.title = data_dict[self.p+"description"][self.p+'title']
			pqa.zip_title = z_thesis
			pqa.pq_id = data_dict[self.p+'description'][self.p+'identifiers']['pubNumber']
			pqa.pq_json = json.dumps(data_dict,indent=4)
			pqa.status = 'attempting-convert'
			pqa.save()
			# open('pq_jsons/'+data_dict[self.p+"description"][self.p+'title'].replace("/","").replace(" ","_")+".json" ,'w').write(json.dumps(data_dict,indent=4))
			pqfs = pqFsAttempt()
			pqfs.pqa_fk = pqa
			pqfs.status = 'attempting-convert'
			pqfs.save()
			figshare_json = self.convert_pq_to_fs(data_dict,pqfs)
			# save converted json in case there's an issue downstream
			
			pqfs.fs_attempt_json = json.dumps(figshare_json,indent=4)
			pqfs.status = 'attempting-push'
			pqfs.save()

			pqa.status = "converted-to-fsjson"
			pqa.save()

			response = requests.post(fs_base_url+'account/articles', params=params, headers=headers, data=json.dumps(figshare_json)).json()
			print(response)
			

			#cleanup
			try: # this should be expanded. there are many other places this can fail. hhhhhhhhhhh
				code = response['code'] #only on error is there a code thrown.
				if response['code'] in ['UnknownException', 'BadRequest', 'UnprocessableEntity']:
					print('NO ARTICLE WAS SAVED OMG')
					print(response['code'])
					# here we should send an email and debug but continue
					pqfs.response = str(response)
					pqfs.status = "failed-at-push"
					pqfs.save()
					pass
				else:
					article_id = response['entity_id']
					pqfs.fs_id = article_id
					pqfs.save()
					print("cool article went through")
					self.rm_user_and_add_file(article_id,upload_file,figshare_json,pqfs)
					os.remove(xml_file)
					os.remove(upload_file)
			except KeyError:
				article_id = response['entity_id']
				pqfs.fs_id = article_id
				pqfs.save()
				self.rm_user_and_add_file(article_id,upload_file,figshare_json,pqfs)
				os.remove(xml_file)
				os.remove(upload_file)
