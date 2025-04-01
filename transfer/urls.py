from django.urls import path
from . import views

urlpatterns = [
    path('oaMessages', views.showMessages, name='showMessages')
    ]