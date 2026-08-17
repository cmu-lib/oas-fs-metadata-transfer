from django.shortcuts import render
from .models import oaMessage,repoLicense,fsAttempt
from django.db.models import Q,F,Value
from django.http import HttpResponse
from django.template import loader
from itertools import chain


def oafsIndex(request): # homepage :)
	return render(request, 'index.html')

def fsAttempts(request): # page to show messages after the attempt to figshare
	fs_attempts = fsAttempt.objects.all().order_by('-id')
	return render(request,'fsAttempts.html',{'attempts':fs_attempts})

def showMessages(request): # page to show messages from oaswitchboard after conversion
	all_messages = oaMessage.objects.all().order_by('-id').select_related('status')
	return render(request, "allMessages.html",{'messages':all_messages})

def showLicenses(request): # page to show licenses from figshare.
	licenses = repoLicense.objects.all()
	return render(request, 'allLicenses.html',{'licenses':licenses})

def allErrors(request):
	fs_errors = fsAttempt.objects.filter(status="failed").annotate(of=Value("Figshare")).values_list('id','oama_fk__message_title', 'status','note','fs_attempt_json','attempted','of').annotate(json=F('fs_attempt_json'))
	oa_errors = oaMessage.objects.filter(status="error").annotate(of=Value("OAS")).values_list('message_id','message_title', 'status','note','message_json','attempted','of').annotate(json=F('message_json'))
	# get these two results as basic lists and merge them together.
	merged_results = list(chain(fs_errors, oa_errors))

	return render(request,'allErrors.html',{"results":merged_results})


# @require_http_methods(['POST'])
def retryOAConversion(request, id):
    Task.objects.filter(id=id).delete()
    tasks = Task.objects.all()
    return render(request, 'tasks_list.html', {'tasks': tasks})


