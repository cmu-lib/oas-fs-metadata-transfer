from django.shortcuts import render
from .models import oaMessage,repoLicense,fsAttempt
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def oafsIndex(request):
	return render(request, 'index.html')

def fsAttempts(request):
	fs_attempts = fsAttempt.objects.all()
	return render(request,'fsAttempts.html',{'attempts':fs_attempts})

def showMessages(request):
	all_messages = oaMessage.objects.all().order_by('id')
	return render(request, "allMessages.html",{'messages':all_messages})

def showLicenses(request):
	licenses = repoLicense.objects.all()
	return render(request, 'allLicenses.html',{'licenses':licenses})