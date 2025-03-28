import secrets
import requests
import json
import time


#PUT INTO FIGSHARE
#####################
#token from figshare#
#####################
headers = {
    'Content-Type': 'application/json',
}

json_data = {
    'client_id': secrets.figshare_client_id,
    'client_secret': secrets.figshare_client_secret,
    'grant_type': 'client_credentials',
}

# response = requests.post('https://api.figsh.com/v2/token', headers=headers, json=json_data).json()
# print(response)
# token = response['token']
# example of the damn thing

f = open("confirmed_article_ids.txt", "w")
f.write('')
f.close()

headers = {
    'Content-Type': 'application/json',
}

params = {
    'access_token': secrets.figshare_token,
}

with open('into_fs.json', 'rb') as f:
    into_messages = json.load(f)

# into_messages = json.load(data)
for i in into_messages:
    print(i)
    print("\n\n")
    response = requests.post('https://api.figsh.com/v2/account/articles', params=params, headers=headers, data=json.dumps(i)).json()
    print(response) 

    try:
        code = response['code']
        if response['code'] in ['UnknownException', 'BadRequest', 'UnprocessableEntity']:
            print('NO ARTICLE WAS SAVED OMG')
            article_up = ""
    except KeyError:
        article_up = str(response['entity_id'])

    f = open("confirmed_article_ids.txt", "a")
    f.write(article_up+',')
    f.close()
    time.sleep(1)
    # my_ass = "2183154"
    # this service automatically adds me as an author which is pretty stupid. i need to remove myself . i found my user ID (for the dev)
    # 2183154
    # by publishing the article and then looking it up https://api.figsh.com/v2/articles/IDOFARTICLE - wouldn't let me see it in private. despite me beingthe owner. awesome.
    # delete my ass to hell out of here.
    # curl -X DELETE "https://api.figshare.com/v2/account/articles/{article_id}/authors/{author_id}"
    # print("deleting \n\n\n")
    # response = requests.delete("https://api.figsh.com/v2/account/articles/"+article_up+"/authors/"+my_ass,params=params,headers=headers)
    # print('\n')
    # print(response.__dict__)

# exit()
# print(response)
my_ass = "2183154"
    # this service automatically adds me as an author which is pretty stupid. i need to remove myself . i found my user ID (for the dev)
    # 2183154
    # by publishing the article and then looking it up https://api.figsh.com/v2/articles/IDOFARTICLE - wouldn't let me see it in private. despite me beingthe owner. awesome.
    # delete my ass to hell out of here.
    # curl -X DELETE "https://api.figshare.com/v2/account/articles/{article_id}/authors/{author_id}"
with open('confirmed_article_ids.txt', 'rb') as f:
        articles = file.read().split(',')
for article in articles:
    print("deleting \n\n\n")
    response = requests.delete("https://api.figsh.com/v2/account/articles/"+str(article)+"/authors/"+my_ass,params=params,headers=headers)
    print('\n')
    print(response.__dict__)
    response = requests.post("https://api.figsh.com/v2/account/articles/"+str(article)+"/private_links",params=params,headers=headers).json()
    print(response)
    print('private link here')
    
