from django.urls import path
from . import views

urlpatterns = [
    path('index', views.oafsIndex, name='oafsIndex'),
    path('oaMessages', views.showMessages, name='showMessages'),
    path('fsAttempts', views.fsAttempts, name='fsAttempts'),
    path('fsLicenses', views.showLicenses, name='showLicenses'),
    path('allErrors', views.allErrors, name='allErrors'),
    ]