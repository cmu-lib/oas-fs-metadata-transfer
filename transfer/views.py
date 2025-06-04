from django.shortcuts import render
from .models import oaMessage,repoLicense,fsAttempt
from django.db.models import Q
from django.http import HttpResponse
from django.template import loader

def oafsIndex(request):
	return render(request, 'index.html')

def fsAttempts(request):
	fs_attempts = fsAttempt.objects.all().order_by('-id')
	return render(request,'fsAttempts.html',{'attempts':fs_attempts})

def showMessages(request):
	all_messages = oaMessage.objects.all().order_by('-id')
	return render(request, "allMessages.html",{'messages':all_messages})

def showLicenses(request):
	licenses = repoLicense.objects.all()
	return render(request, 'allLicenses.html',{'licenses':licenses})

def	fsPushResults(request):
	fs_push_results = fsAttempt.objects.filter(Q(status='failed')|Q(status='ready-for-review')).order_by('-id')
	return render(request,'fsPushResults.html',{'attempts':fs_push_results})
	# 787          (Q(start_display__lte=timezone.now()) | Q(start_display=None)) &
# 	pages = models.Page.objects.filter(
   # 43          content_type=request.model_content_type,
   # 44          object_id=request.site_type.pk,
   # 45      )