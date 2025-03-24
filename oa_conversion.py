import secrets
import requests
import json

#messages from OA SWITCHBOARD
#################
# oa_token first#
#################
# headers = {
#     'Content-Type': 'application/json',
# }

# json_data = {
#     'email': secrets.oa_switchboard_email,
#     'password': secrets.oa_switchboard_pw,
# }

# oa_token_response = requests.post('https://api.oaswitchboard.org/v2/authorize', headers=headers, json=json_data)

# response is like this 
# {
#   "token": "",
#   "participant": {
#     "id": ###,
#     "organisation": "Carnegie Mellon University",
#     "cognito_id": "##-#-4dab-9b35-##",
#     "email": "",
#     "fullname": null,
#     "type": "institution"
#   }
# }
################
# token for now# 
################
# oa_token = oa_token_response['token']
# headers = {
#     'Authorization': 'Bearer '+oa_token+'',
# }

# params = {
#     'startrow': '1',
#     'maxrows': '25',
#     'filter': 'all',
#     'orderby': 'created',
#     'orderdir': 'desc',
# }

# oa_messages = requests.get('https://api.oaswitchboard.org/v2/messages', params=params, headers=headers).json()
oa_messages = ""
with open('messages.json') as f:
    oa_messages = json.load(f)

license_list = ""
with open('sandbox_licenses.json') as f:
    license_list = json.load(f)

# print(oa_messages)

# notes from feb 26 say
# authors
#     orcid, dept affiliation up to first comma, ln fn
# article
#     grant #, publication date in manuscript, license, don't mint new doi but save that. all item type = journal contribution.

def getval(dictionary,key): #stupid function for keyerror try catch.
    try:
        return dictionary[key]
    except KeyError:
        return  ""

message_counter = 0
f = open("into_fs.json", "w")
f.write("[")
for message in oa_messages['messages']:
    message_counter+=1
    message_to_fs = {"authors":[],"funding_list":[],"title":"","published_date":"","status":"published","license":{},"doi":""}
    # let's get authors
    authors = message['data']['authors']

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
        fn = getval(this_guy,'lastName')
        ln = getval(this_guy,'firstName')
        ini = getval(this_guy,'initials')
        orcid = getval(this_guy,'ORCID')
        inst = getval(this_guy,'institutions')
        print(inst) # ex [{'name': 'Departmentof Biomedical Engineering, Carnegie MellonUniversity, Pittsburgh, Pennsylvania, United States, 15213', 'country': '', 'sourceaffiliation': '', 'ror': 'https://ror.org/05x2bcf33'}]
        inst = getval(inst[0],'name').split(',')[0]
        # where does inst go???
        author_dict = {"full_name":fn+" "+ln,"first_name":fn,"last_name":ln,"orcid_id":orcid}
        message_to_fs['authors'].append(author_dict)
    # let's get articles
    article = message['data']['article']

    title = article['title']
    message_to_fs['title'] = title

    publication_date = getval(article['manuscript']['dates'],'publication')
    message_to_fs['published_date']=publication_date

    license = article['vor']['license']
    for pre_license in license_list:
        if license == pre_license['name']:
            license = pre_license['value']
            break
        else:
            license=0
            print("\nthere's no matching license here!!!!\n")

    message_to_fs['license']={"value":1,"name":license}
# {
# "value": 1,
# "name": "CC BY",
# "url": "http://creativecommons.org/licenses/by/4.0/"
# }
    doi = article['doi']
    message_to_fs['doi']=doi

    if len(getval(article,'grants'))>0:
        for grant in article['grants']:
            print(grant['name']) # idk if this is what we want or if it's something else and how to put it into the fs.  there is funding_list and also funding . waiting t ohear back.
            message_to_fs['funding_list'].append({"grant_code":grant['name']})
    f = open("into_fs.json", "a")
    f.write(json.dumps(message_to_fs))

    if len(oa_messages['messages'])==message_counter:
        f.close()
        break
    else:
        f.write(',')
    f.close()
f = open("into_fs.json", "a")
f.write(']')
f.close()
# lastName
# firstName
# initials
# ORCID

#PUT INTO FIGSHARE
#####################
#token from figshare#
#####################


# headers = {
#     'Content-Type': 'application/json',
# }

# json_data = {
#     'client_id': secrets.figshare_client_id,
#     'client_secret': secrets.figshare_client_secret,
#     'grant_type': 'client_credentials',
# }

# response = requests.post('https://api.figsh.com/v2/token', headers=headers, json=json_data)

#response is the token.

# use the token to do the insert with the other thing. FORTHCOMING