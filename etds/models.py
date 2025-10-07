from django.db import models

class pqAttempt(models.Model): 
    zip_title = models.CharField(max_length=1024, help_text='title of the zip',null=True)
    pq_id = models.IntegerField(help_text="id of the preprint",default=0)
    pq_json = models.TextField(help_text="the json convert",null=True)
    title = models.CharField(max_length=2048, help_text="title of the preprint",null=True)
    received = models.DateTimeField(auto_now_add=True, blank=True)
    note = models.TextField(help_text="what went wrong. what went write.",default="",null=True)
    status = models.CharField(max_length=2048, help_text="status and maybe error message",null=True,default='ready-for-push')
    
    def __str__(self):
        return self.title

class pqFsAttempt(models.Model): 
    pqa_fk = models.ForeignKey('pqAttempt', on_delete=models.CASCADE ,help_text='FK for pqAttempt') 
    fs_id = models.IntegerField(help_text="filled in after successful upload to figshare",default=0)
    # statuses: ['ready-for-push','ready-for-review','failed','published']
    status = models.CharField(max_length=2048, help_text="status and maybe error message",null=True,default='ready-for-push')
    response = models.CharField(max_length=2048, help_text="response status from FS",null=True,default='')
    link = models.CharField(max_length=1024, help_text="link created for reference on fs",null=True)
    attempted= models.DateTimeField(auto_now_add=True, blank=True)
    note = models.TextField(help_text="what went wrong. what went write.",default="",null=True)
    fs_attempt_json = models.TextField(help_text="the json attempt",null=True)
    
    def __str__(self):
        return self.pqa_fk.title

class fsToken(models.Model): 
    token = models.CharField(max_length=2048, help_text="the token",null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True)
    
    def __str__(self):
        return self.token