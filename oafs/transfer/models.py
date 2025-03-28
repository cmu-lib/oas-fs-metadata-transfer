from django.db import models
from django import forms


class oaMessage(models.Model):  # base class should subclass 'django.db.models.Model'
    message_id = models.IntegerField(help_text="id of the messages")
    message_title = models.CharField(max_length=1024, help_text='title of the article')
    status = models.CharField(max_length=2048, help_text="status and maybe error message")
    attempted = models.DateTimeField(auto_now_add=True, blank=True)
    message_json = models.TextField(help_text="the json received")
    
    def __str__(self):
        return self.message_title
    
class fsAttempt(models.Model):  
	oa_id = models.ForeignKey('oaMessage', on_delete=models.CASCADE ,help_text='FK for token table')
	fs_id = models.IntegerField(help_text="filled in after successful upload to figshare")
	status = models.CharField(max_length=2048, help_text="status and maybe error message")
	link = models.CharField(max_length=1024, help_text="link created for reference on fs")
	fs_attempt_json = models.TextField(help_text="the json attempt")