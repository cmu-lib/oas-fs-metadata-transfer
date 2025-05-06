from django.urls import path
from . import views

urlpatterns = [
    path('index', views.oafsIndex, name='oafsIndex'),
    path('oaMessages', views.showMessages, name='showMessages')
    ]