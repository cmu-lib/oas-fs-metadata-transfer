import requests
import json

params = {
    'access_token': , #add access token here
}

our_licenses = requests.get('https://api.figsh.com/v2/account/licenses', params=params).json()

