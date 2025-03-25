i don't think this needs to be more complicated than a single script. for right now just concerned about getting things from oa into fs.
perhaps we may want to save the IDs and determine which messages have been saved/transferred successfully and we can compare that against what's coming in...
unclear at this point.
but if this does need to be more robust i can see it being a small django app so emily and katie can review it would have:

- links to the articles 
- saved in a db (only metadata so nbd)
	- for that matter what happens when these articles are updated?
	- ya not sure how oa switchboard would be messaging about updated articles, if those do happen... 

but let's just get it working


available licenses in our api. need to be accessed by the api.
accessed like this `curl -X GET "https://api.figsh.com/v2/account/licenses?`
need to do this separately and then match 

ugh