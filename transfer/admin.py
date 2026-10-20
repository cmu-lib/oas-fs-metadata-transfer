from django.contrib import admin
from .models import useDevSettings, serviceCredentials  # Import your model here

admin.site.register(useDevSettings)
admin.site.register(serviceCredentials)