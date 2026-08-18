from django.db import models
from django import forms


# so you can modify this in the admin  
class serviceCredentials(models.Model):
    token = models.CharField(max_length=1024, help_text='token for whatever',null=True, blank=True)
    token_created = models.DateTimeField(auto_now_add=True, blank=True)
    name = models.CharField(max_length=1024, help_text='name for the service',null=False)
    client_id = models.CharField(max_length=1024, help_text='client id for whatever',null=False)
    client_secret = models.CharField(max_length=1024, help_text='client secret for whatever',null=False)
    is_dev = models.BooleanField(help_text='is this a dev token?',default=False)
    url = models.CharField(max_length=1024, help_text='url pointed at for the api calls. ie https://api.figshare.com/v2/ (make sure to include final "/")',null=True)
    def __str__(self):
        return self.name + " (Dev)" if self.is_dev else self.name + " (Prod)"

class useDevSettings(models.Model):
    use_dev = models.BooleanField(help_text='use dev settings?',default=False)
    def __str__(self):
        return "Using Dev Settings" if self.use_dev else "Using Production Settings"

class oaMessage(models.Model):  
    oa_id = models.IntegerField(help_text="id of the messages",default=0)
    title = models.CharField(max_length=1024, help_text='title of the article',null=True)
    attempted = models.DateTimeField(auto_now_add=True, blank=True)
    json = models.TextField(help_text="the json received",default=None,null=True)
    
    def __str__(self):
        return self.title

# specific to figshare
class repoLicense(models.Model):
    value = models.CharField(max_length=1024, help_text='cc short code',null=True,unique=True)
    name = models.CharField(max_length=1024, help_text='longform',null=True,unique=True)
    url = models.CharField(max_length=1024, help_text='url for this license',null=True)
    def __str__(self):
        return self.name
        
class fsAttempt(models.Model):  
    oam_fk = models.ForeignKey('oaMessage', on_delete=models.CASCADE ,help_text='FK for oamessage') #oaMessageAttempt
    fs_id = models.IntegerField(help_text="filled in after successful upload to figshare",default=0)
    doi = models.CharField(max_length=123, help_text="for comparing duplicate/revisions",null=False,default='0')
    response = models.CharField(max_length=2048, help_text="response status from FS",null=True,default='')
    link = models.CharField(max_length=1024, help_text="link created for reference on fs",null=True)
    attempted= models.DateTimeField(auto_now_add=True, blank=True)
    json = models.TextField(help_text="the json attempt",null=True)
    
    def __str__(self):
            return self.oam_fk.title + " fs_id: " + str(self.fs_id)

#general statuses/notes for both an oaMessage and fsAttempt if related.
class messageStatus(models.Model):
    note = models.TextField(help_text="what went wrong. what went right.",default="",null=True)
    type = models.CharField(max_length=256, help_text="type of error.",default="",null=True)
    status = models.CharField(max_length=256, help_text="type of error.",default="",null=True) # during the oa intake, during the conversion, during the push to figshare, etc.
    fs = models.ForeignKey('fsAttempt', null=True, on_delete=models.CASCADE ,help_text='FK for fs', related_name='status')
    oa = models.ForeignKey('oaMessage', null=True, on_delete=models.CASCADE ,help_text='FK for oa', related_name='status')
    
    # user_fk = models.ForeignKey('orcidUser', null=True, on_delete=models.CASCADE ,help_text='FK for users') #oaMessageAttempt
    
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
