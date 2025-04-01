from django.shortcuts import render
from .models import oaMessage
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def showMessages(request):
	all_messages = oaMessage.objects.all()
	return render(request, "allMessages.html",{'messages':all_messages})