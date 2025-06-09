from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
	def handle(self,*args,**options):
		call_command('get_licenses',*args,**options)
		call_command('get_oa_messages',*args,**options)
		call_command('convert_oa_to_fs',*args,**options)
		call_command('push_to_fs',*args,**options)
		