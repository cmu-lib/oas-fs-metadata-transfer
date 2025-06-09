cronjob runs `transfer/management/commands/do_everything.py`


- do_everything 
	- get licenses from figshare
	- get the latest oa messages, you can change setting of how many at a time in settings.how_many_oa_messages
	- convert the oa messages to a json format that figshare likes
	- try to push those converted messages to figshare

the next step will be going to check manually on figshare and also check manually here for other issues that occured in trying to process the oa switchboard messages and in the attempts to push those formatted messages to figshare.


https://bitbucket.org/oaswitchboard/api/src/master/README.md
https://docs.figshare.com/