from django.utils import timezone
from django.db.models import Q
import datetime, requests
from transfer.models import useDevSettings, serviceCredentials


def handle_mess(status, note, mess):
    mess.status = status
    mess.note = note
    mess.save()
    return mess

def get_val(dictionary,key): #simple function for keyerror try catch.
        try:
            return dictionary[key]
        except KeyError:
            return  0

def get_token(service_name):
    print(service_name)
    is_dev = useDevSettings.objects.first()
    if is_dev.use_dev:
        access  = serviceCredentials.objects.filter(is_dev=True, name=service_name).first()
        print('just so you know, you have this on DEVELOPMENT settings.')
    else:
        access  = serviceCredentials.objects.filter(is_dev=False, name=service_name).first()
        print('just so you know, this is on PRODUCTION settings.')
    # if you ain't got nothing then return nothin.
    if access  is None:
        print('no credentials found for this service. please add them in the admin.')
        return ""

    # let's see how long ago the last token was created.
    token_time = datetime.datetime.fromisoformat(str(access.token_created))
    if (timezone.now() - token_time).total_seconds() < 3500 and access.token is not None: #tokens last an hour, so if it's been less than 3500 seconds just use it.
        return access
    else:
        # make a new token.
        headers = {
            'Content-Type': 'application/json',
        }

        if service_name == "oafigshare":
            json_data = {
                        'client_id': access.client_id,
                        'client_secret': access.client_secret,
                        'grant_type': 'client_credentials',
                    }
            token_response = requests.post(access.url+'token', headers=headers, json=json_data).json()
            # self.stdout.write(json.dumps(token_response))
            access.token = token_response['token']
            access.token_created = timezone.now()
            access.save()
            return access
        elif service_name == "oaswitchboard":
            json_data = {
                        'email': access.client_id,
                        'password': access.client_secret,
                    }
            token_response = requests.post(access.url+'authorize', headers=headers, json=json_data).json()
            # self.stdout.write(json.dumps(token_response))
            access.token = token_response['token']
            access.token_created = timezone.now()
            access.save()
            return access
        elif service_name == "psqfigshare":
            json_data = {
                        'client_id': access.client_id,
                        'client_secret': access.client_secret,
                        'grant_type': 'client_credentials',
                    }
            token_response = requests.post(access.url+'token', headers=headers, json=json_data).json()
            # self.stdout.write(json.dumps(token_response))
            access.token = token_response['token']
            access.token_created = timezone.now()
            access.save()
            return access
        else:
            print('no service name provided. please provide a service name.')
            return ""

# if a name is improperly spelled or does not match EXACTLY or already exists in figshare then it won't work.
# using the provided orcid, if it exists, get the authorID from figshare and just submit them with that. 
def check_orcid_user_in_fs(orcid_id):
    access  = get_token("oafigshare")
    headers = {
        'Content-Type': 'application/json',
    }
    params = {
        'access_token': access.token,
    }
    response = requests.post(access.url+'account/authors/search', params=params, headers=headers, data='{"orcid":"'+orcid_id+'"}').json()
    if len(response) > 0:
        return {'id': response[0]['id']}
    else:
        return 0