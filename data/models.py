from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
	user = models.OneToOneField(User)
	""" default user attributes:
		username
		password
		email
		first/last name
	"""
	meetings_in = models.ManyToManyField('Meeting', null=True, blank=True)
	meetings_created = models.ManyToManyField('Meeting', null=True, blank=True)
	join_date = models.DateField()
	prof_pic = models.ImageField(upload_to='photos', blank=True, default=False)
	phone = models.CharField(max_length=20)
	contacts = models.ManyToManyField('self', blank=True, null=True)

class Meeting(models.Model):
	members = models.ManyToManyField('Account', null=True, blank=True)
	moderators = models.ManyToManyField('Account', null=True, blank=True)
	hosts = models.ManyToManyField('Account')
	start = models.DateTimeField()
	end = models.DateTimeField()
	title = models.CharField(max_length=50) # these are arbitrary
	desc = models.CharField(max_length=500)
	private = models.BooleanField()
	meeting_id = models.CharField()
	agenda_items = models.ManyToManyField('AgendaItem', null=True, blank=TRue)

class AgendaItem(models.Model):
	name = models.CharField(max_length=50)
	desc = models.CharField(max_length=100) # is this needed?
	motions = models.ManyToManyField('Motion', null=True, blank=True)

class Motion(models.Model):
	user = models.ForeignKey('Account')
	timestamp = models.DateTimeField()
	name = models.CharField(max_length=50)
	desc = models.CharField(max_length=500)
	likes = models.IntegerField()
	dislikes = models.IntegerField()
	comments = models.ManyToManyField('Comment', null=True, blank=True)

class Comment(models.Model):
	user = models.ForeignKey('Account')
	timestamp = models.DateTimeField()
	text = models.CharField(max_length=500)

