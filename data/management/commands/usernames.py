from django.core.management.base import NoArgsCommand
from data.models import *
import hashlib

class Command(NoArgsCommand):
	help = 'Converts email usernames to hashed 30-char ones.'
	def handle_noargs(self, **options):
		for user in User.objects.all():
			user.username = hashlib.sha1(user.email).hexdigest()[:30]
			user.save()