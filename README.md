# intro

this was originally just for cmu to move messages from oaswitchboard to figshare as metadata, hence the name. 

now, this app is meant to be a vaugely general framework/guideline for taking in items via an API, converting them and, moving them to another place. it needs to be renamed but i am unsure exactly what to name it.

the impetus to make it more general was from interest from the oaswitchboard community to share code and to accommodate another project where we take in deposits from proquest and put them to figshare for our electronic theses and dissertations.

on the CLEAN branch we have an example of oaswitchboard -> figshare but it should be default-enough for one to use it for their own purposes with some customizations..

### setup

install this app into a virtual environment -- `mkvirtualenv nameofenv --python=/usr/bin/python3.10` (currently using python 3.10.12) and `workon nameofenv`
run the `pip install -r requirements.txt`
create superuser `./manage.py createsuperuser` and follow those instructions.

- /oafs/secrets.json
this only contains the django SECRET_KEY but you can use it if there are other variables you want to separate and keep hidden. it is referenced in /oafs/settings.py

run `./manage runserver`
go to localhost:8000/admin
login using the superuser credentials
add one entry to the useDevSettings and modify it if you are working in a dev or prod setting
add as many entries as you'd like or want to use for the apis you will be handling for serviceCredentials
! client_id and secret for oaswitchboard are *email* and *pw*. this is handled in utils.get_token function dependent upon the service being used..

- /oafs/settings.py
some variables in here that can be public across applications


### for oaswitchboard -> xxxxxxx

to whatever you want!
feel free to use the figshare app as an example for yourself. 
you basically just need get_oa_messages.py  and then it's up to you how to process it.
the entire json response is saved during this process, and a separate tracking note is saved to determine status or other errors that may occur.

### for oaswitchboard -> figshare

- /oafs/transfer/settings.py
variables for this specific app (oaswitchboard -> figshare) which you may not need. 
`institution_ror` to make certain that relevant oa messages are coming through
`how_many_oa_messages` limit on the call for more messages

cronjob runs `transfer/management/commands/do_everything.py`

- do_everything 
	- get the latest oa messages (get_oa_messages)
	- get licenses from figshare (get_licenses)
	- convert the oa messages to a json format that figshare likes (convert_oa_to_fs)
	- try to push those converted messages to figshare (push_to_fs)

there are a couple scripts for cleaning up (killem_alll)

results are at http://DOMAIN/oafs/fsAttempts and  http://DOMAIN/oafs/oaMessages

### for proquest -> figshare

- /oafs/etds/settings.py
variables just for this (this is how we do the thesis submission.)

- we get deposits from them into a folder that is symlink'd within this repo @ `/etds/zippies`
- cronjob runs `etds/management/commands/extract_convert_push_pq.py`

results at http://DOMAIN/etds/attempts

https://bitbucket.org/oaswitchboard/api/src/master/README.md
https://docs.figshare.com/