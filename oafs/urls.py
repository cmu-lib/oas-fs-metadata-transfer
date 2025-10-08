"""
URL configuration for oafs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from transfer.views import oafsIndex, fsAttempts, showMessages, showLicenses, allErrors, retryOAConversion
from etds.views import pqFsAttempts

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', oafsIndex, name='oafsIndex'),
    path('fsAttempts', fsAttempts, name='fsAttempts'),
    path('oaMessages', showMessages, name='showMessages'),
    path('fsLicenses', showLicenses, name='showLicenses'),
    path('allErrors', allErrors, name='allErrors'),
    path('proquest/attempts', pqFsAttempts, name='pqFsAttempts'),
    path('<int:key_id>/', retryOAConversion, name='retryOAConversion'),
]
