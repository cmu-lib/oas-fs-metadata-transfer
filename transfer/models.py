from django.db import models
from django import forms

# i think this should be like a cursor. would it be better to have this saved as a file then?
# the oa messages have failed on me a couple times when trying to make more than a couple requests

#instead of doing NOTES here i think maybe have some other sort of table that will have "issues" as these can resolve.
class oaMessageAttempts(models.Model): 
    attempted = models.DateTimeField(auto_now_add=True, blank=True)
    total_messages = models.IntegerField(help_text="how many messages we gots", default=0)
    last_offset = models.IntegerField(help_text="how far back", default=0)

class repoLicense(models.Model):
    value = models.CharField(max_length=1024, help_text='cc short code',null=True,unique=True)
    name = models.CharField(max_length=1024, help_text='longform',null=True,unique=True)
    url = models.CharField(max_length=1024, help_text='url for this license',null=True)
    def __str__(self):
        return self.name

class oaMessage(models.Model):  
    message_id = models.IntegerField(help_text="id of the messages",default=0)
    message_title = models.CharField(max_length=1024, help_text='title of the article',null=True)
    # statuses: ['transferred','ignore','error','ready','duplicate']
    status = models.CharField(max_length=2048, help_text="status and maybe error message",null=True,default='ready')
    note = models.TextField(help_text="what went wrong. what went write.",default="",null=True)
    attempted = models.DateTimeField(auto_now_add=True, blank=True)
    message_json = models.TextField(help_text="the json received",default=None,null=True)
    
    def __str__(self):
        return self.message_title
    
class fsAttempt(models.Model):  
    oama_fk = models.ForeignKey('oaMessage', on_delete=models.CASCADE ,help_text='FK for oamessage') #oaMessageAttempt
    fs_id = models.IntegerField(help_text="filled in after successful upload to figshare",default=0)
    # statuses: ['ready-for-push','ready-for-review','failed','published']
    status = models.CharField(max_length=2048, help_text="status and maybe error message",null=True,default='ready-for-push')
    response = models.CharField(max_length=2048, help_text="response status from FS",null=True,default='')
    link = models.CharField(max_length=1024, help_text="link created for reference on fs",null=True)
    attempted= models.DateTimeField(auto_now_add=True, blank=True)
    note = models.TextField(help_text="what went wrong. what went write.",default="",null=True)
    fs_attempt_json = models.TextField(help_text="the json attempt",null=True)

# class orcidUser(models.Model):
#     f_name = models.CharField(max_length=512,help_text="whats yo name")
#     l_name = models.CharField(max_length=512,help_text="who's yo daddy")
#     full_name = models.CharField(max_length=512)
#     from_orcid = models.CharField(max_length=256,default="") #is this current name from orcid
#     orcid_x_attempted = models.DateTimeField(auto_now_add=False, default=None,null=True)
#     #status should be fk?
#     status = models.CharField(max_length=2048, help_text="status in case of error on user",null=True)
#     # inst = models.CharField(max_length=512)
#     orcid = models.CharField(max_length=256,null=True,default=None)
#     # the id from figshare.
#     fs_id = models.IntegerField(default=0)
#     # if we find this user again we can add him/her/zim to other articles.
#     articles = models.ManyToManyField(fsAttempt)

# class orcidUserAlts(models.Model):
#     ou_fk = models.ForeignKey('orcidUser',on_delete=models.CASCADE)
#     f_name = models.CharField(max_length=512)
#     l_name = models.CharField(max_length=512)
#     full_name = models.CharField(max_length=512)

# class errorMsg(models.Model):
#     note = models.TextField(help_text="what went wrong. what went right.",default="",null=True)
#     type = models.CharField(max_length=256, help_text="type of error.",default="",null=True)
#     oama_fk = models.ForeignKey('oaMessage',null=True, on_delete=models.CASCADE ,help_text='FK for oa ') #oaMessageAttempt
#     fs_fk = models.ForeignKey('fsAttempt', null=True, on_delete=models.CASCADE ,help_text='FK for fs') #oaMessageAttempt
#     user_fk = models.ForeignKey('orcidUser', null=True, on_delete=models.CASCADE ,help_text='FK for users') #oaMessageAttempt
#     level = models.IntegerField(default=0)
#     