from django.utils import timezone
import datetime, requests
from transfer.models import useDevSettings, serviceCredentials, messageStatus

def organize_statuses(all_messages):
    for mess in all_messages:
        mess.statuses = messageStatus.objects.filter(oa=mess)

        if(len(mess.statuses)>1):
            mess.overall_status = "multiple errors/statuses"
        else:
            for i in mess.statuses:
                print(i.status)
                if i.status == "error":
                    mess.overall_status = "error"
                    break
                elif i.status == "duplicate":
                    mess.overall_status = "duplicate"
                elif i.status == "begin":
                    mess.overall_status = "begin"
                elif i.status == "oa-ready":
                    mess.overall_status = "oa-ready"
                else:
                    mess.overall_status = "unknown"
    return all_messages

def get_val(dictionary,key): #simple function for keyerror try catch.
        try:
            return dictionary[key]
        except KeyError:
            return  '!!missing!!'

def get_token(service_name):
    print(service_name)
    is_dev = useDevSettings.objects.first()
    if is_dev.use_dev:
        sc = serviceCredentials.objects.filter(is_dev=True, name=service_name).first()
        print('just so you know, you have this on DEVELOPMENT settings.')
    else:
        sc = serviceCredentials.objects.filter(is_dev=False, name=service_name).first()
        print('just so you know, this is on PRODUCTION settings.')
    # if you ain't got nothing then return nothin.
    if sc is None:
        print('no credentials found for this service. please add them in the admin.')
        return ""

    # let's see how long ago the last token was created.
    token_time = datetime.datetime.fromisoformat(str(sc.token_created))
    if (timezone.now() - token_time).total_seconds() < 3500 and sc.token is not None: #tokens last an hour, so if it's been less than 3500 seconds just use it.
        return sc
    else:
        # make a new token.
        headers = {
            'Content-Type': 'application/json',
        }

        if service_name == "oafigshare":
            json_data = {
                        'client_id': sc.client_id,
                        'client_secret': sc.client_secret,
                        'grant_type': 'client_credentials',
                    }
            token_response = requests.post(sc.url+'token', headers=headers, json=json_data).json()
            # self.stdout.write(json.dumps(token_response))
            sc.token = token_response['token']
            sc.token_created = timezone.now()
            sc.save()
            return sc
        elif service_name == "oaswitchboard":
            json_data = {
                        'email': sc.client_id,
                        'password': sc.client_secret,
                    }
            token_response = requests.post(sc.url+'authorize', headers=headers, json=json_data).json()
            # self.stdout.write(json.dumps(token_response))
            sc.token = token_response['token']
            sc.token_created = timezone.now()
            sc.save()
            return sc
        elif service_name == "psqfigshare":
            json_data = {
                        'client_id': sc.client_id,
                        'client_secret': sc.client_secret,
                        'grant_type': 'client_credentials',
                    }
            token_response = requests.post(sc.url+'token', headers=headers, json=json_data).json()
            # self.stdout.write(json.dumps(token_response))
            sc.token = token_response['token']
            sc.token_created = timezone.now()
            sc.save()
            return sc
        else:
            print('no service name provided. please provide a service name.')
            return ""