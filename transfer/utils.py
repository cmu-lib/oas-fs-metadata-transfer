import datetime, timezone, requests

def get_token(name):
    useDevSettings = useDevSettings.objects.first()
    if useDevSettings.use_dev:
        serviceCredentials = serviceCredentials.objects.filter(is_dev=True, name=name).first()
        print('just so you know, you have this on DEVELOPMENT settings.')        
    else:
        serviceCredentials = serviceCredentials.objects.filter(is_dev=False, name=name).first()
        print('just so you know, this is on PRODUCTION settings.')

    # if you ain't got nothing then return nothin.
    if serviceCredentials is None:
        print('no credentials found for this service. please add them in the admin.')
        return ""
    
    # let's see how long ago the last token was created.
    token_time = datetime.datetime.fromisoformat(str(serviceCredentials.token_created))
    if (timezone.now() - token_time).total_seconds() < 3500: #tokens last an hour, so if it's been less than 3500 seconds just use it.
        return(serviceCredentials.token)
    else:
        # make a new token.
        headers = {
            'Content-Type': 'application/json',
        }

        json_data = {
            'client_id': serviceCredentials.client_id,
            'client_secret': serviceCredentials.client_secret,
            'grant_type': 'client_credentials',
        }

        fs_token_response = requests.post(serviceCredentials.url+'token', headers=headers, json=json_data).json()
        # self.stdout.write(json.dumps(fs_token_response))
        serviceCredentials.token = fs_token_response['token']
        serviceCredentials.token_created = timezone.now()
        serviceCredentials.save()
        return serviceCredentials