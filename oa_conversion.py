import secrets
import requests
import json

#messages from OA SWITCHBOARD

oa_token first#
headers = {
    'Content-Type': 'application/json',
}

json_data = {
    'email': oa_switchboard_email,
    'password': oa_switchboard_pw,
}

oa_token_response = requests.post('https://api.oaswitchboard.org/v2/authorize', headers=headers, json=json_data)

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

# token for now 
oa_token = oa_token_response['token']
headers = {
    'Authorization': 'Bearer '+oa_token+'',
}

params = {
    'startrow': '1',
    'maxrows': '25',
    'filter': 'all',
    'orderby': 'created',
    'orderdir': 'desc',
}

oa_messages = requests.get('https://api.oaswitchboard.org/v2/messages', params=params, headers=headers).json()
# oa_messages = ""
# with open('ex_msgs.json') as f:
#     oa_messages = json.load(f)

# print(oa_messages)

# notes from feb 26 say
# authors
#     orcid, dept affiliation up to first comma, ln fn
# article
#     grant #, publication date in manuscript, license, don't mint new doi but save that. all item type = journal contribution.
def getval(dictionary,key):
    try:
        return dictionary[key]
    except KeyError:
        return  ""

for message in oa_messages['messages']:
    
    # let's get authors
    authors = message['data']['authors']

    for this_guy in authors:
        print(getval(this_guy,'lastName'))
        
        print(getval(this_guy,'firstName'))
        print(getval(this_guy,'initials'))
        print(getval(this_guy,'ORCID'))
        inst = getval(this_guy,'institutions')
        print(inst) # ex [{'name': 'Departmentof Biomedical Engineering, Carnegie MellonUniversity, Pittsburgh, Pennsylvania, United States, 15213', 'country': '', 'sourceaffiliation': '', 'ror': 'https://ror.org/05x2bcf33'}]
        print(getval(inst[0],'name').split(',')[0])
    # let's get articles
    article = message['data']['article']
    title = article['title']
    publication = article['manuscript']['dates']['publication']
    license = article['vor']['license']
    doi = article['doi']
    for grant in article['grants']:
        print(grant['name'])

        
# lastName
# firstName
# initials
# ORCID

#PUT INTO FIGSHARE
#####################
#token from figshare#
#####################
headers = {
    'Content-Type': 'application/json',
}

json_data = {
    'client_id': figshare_client_id,
    'client_secret': figshare_client_secret,
    'grant_type': 'client_credentials',
}

response = requests.post('https://api.figsh.com/v2/token', headers=headers, json=json_data)

#response is the token.

# use the token to do the insert with the other thing. FORTHCOMING