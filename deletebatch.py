import requests
import json

headers = {
    'Content-Type': 'application/json',
}

params = {
    'access_token': '',
}

json_data = {}

response = requests.post('https://api.figsh.com/v2/account/articles/search', params=params, headers=headers, json=json_data).json()

for x in response:
    print(x['id'])
    response = requests.delete('https://api.figsh.com/v2/account/articles/'+str(x['id']),params=params,headers=headers)
    print(response.__dict__)
    print('goodbye, dirtbag')