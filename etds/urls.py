from django.urls import path
from etds.views import pqFsAttempts

urlpatterns = [
    path('attempts', pqFsAttempts, name='pqFsAttempts'),
]
