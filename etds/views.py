from django.shortcuts import render
from etds.models import pqFsAttempt

def pqFsAttempts(request): # page to show messages after the attempt to figshare
	pqfs_attempts = pqFsAttempt.objects.all().order_by('-id')
	return render(request,'pqFsAttempts.html',{'attempts':pqfs_attempts})
