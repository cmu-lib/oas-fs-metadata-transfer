# intro

this was originally just for cmu to move messages from oaswitchboard to figshare as metadata, hence the name. 

now, this app is meant to be a vaugely general framework/guideline for taking in items via an API, converting them and, moving them to another place. it needs to be renamed but i am unsure exactly what to name it.

the impetus to make it more general was from interest from the oaswitchboard community to share code and to accommodate another project where we take in deposits from proquest and put them to figshare for our electronic theses and dissertations.

on the CLEAN branch we have an example of oaswitchboard -> figshare but it should be default-enough for one to use it for their own purposes with some customizations..

### setup

1. install this app into a virtual environment -- `mkvirtualenv nameofenv --python=/usr/bin/python3.10` (currently using python 3.10.12) and `workon nameofenv`
2. run the `pip install -r requirements.txt`
3. create superuser `./manage.py createsuperuser` and follow those instructions.

- /oafs/secrets.json
this only contains the django SECRET_KEY but you can use it if there are other variables you want to separate and keep hidden. it is referenced in /oafs/settings.py on line 18.

4. run `./manage runserver`
5. go to localhost:8000/admin
6. login using the superuser credentials you created in 3.
7. add one entry to the useDevSettings. modify it depending on if you are working in a dev or prod setting
8. add as many entries as you'd like or want to use for the apis you will be handling for serviceCredentials
for instance 

we have credentials for the dev version of oaswitchboard which look like this:

- name - "oaswitchboard" 
	- depending on the name you will have to change transfer.utils.py and get_oa_messages.py to handle the different service for get_token().
- url: "https://api.oaswitchboard.org/v2/"
	- this may change if you have dev or prod envs.
- client_id: "(shh)"
- client_secret: "(shhh!)"
- token: (leave this blank)
	- is saved to on creation of token. if it's more than hour old, a new one is created so you don't overwhelm the service.
- is_dev: on, if these are credentials for your dev instance of the service.
!! client_id and secret for oaswitchboard are *email* and *pw*. this is handled in transfer.utils.get_token() function dependent upon the service being used.!!

make another one for where you want to send it.

- /oafs/settings.py
some variables in here that can be public across applications

### for oaswitchboard -> xxxxxxx

to whatever you want!
feel free to use the transfer app as an example for yourself. 
you basically just need get_oa_messages.py  and then it's up to you how to process it.
the entire json response is saved during this process so you can use this for other purposes.


### for oaswitchboard -> figshare

- /oafs/transfer/settings.py
variables for this specific app (oaswitchboard -> figshare) which you may not need. 
`institution_ror` to make certain that relevant oa messages are coming through
`how_many_oa_messages` limit on the call for more messages (set to 50 default.)

cronjob runs `transfer/management/commands/do_everything.py`

- do_everything 
	- get the latest oa messages (get_oa_messages)
	- get licenses from figshare (get_licenses)
	- convert the oa messages to a json format that figshare likes (convert_oa_to_fs)
		- analyzes the json file and extracts the specific variables for the figshare api post. use this as an example on how to push to your own service (zenodo, researchgate, w/e)
	- try to push those converted messages to figshare (push_to_fs)
		- push the json you created in conversion to figshare.

results are at http://DOMAIN/oafs/fsAttempts and  http://DOMAIN/oafs/oaMessages
