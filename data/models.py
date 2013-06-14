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
	meetings_in = models.ManyToManyField('Meeting', related_name="meetings_in_set", null=True, blank=True)
	meetings_created = models.ManyToManyField('Meeting', related_name="meetings_created_set", null=True, blank=True)
	join_date = models.DateField()
	prof_pic = models.ImageField(upload_to='photos', blank=True, default=False)
	phone = models.CharField(max_length=20)
	contacts = models.ManyToManyField('self', blank=True, null=True)

class Meeting(models.Model):
	members = models.ManyToManyField('Account', related_name="members_set", null=True, blank=True)
	moderators = models.ManyToManyField('Account', related_name="mods_set", null=True, blank=True)
	hosts = models.ManyToManyField('Account', related_name="host")
	startdate = models.DateField()
	starttime = models.TimeField()
	enddate = models.DateField()
	endtime = models.TimeField()
	title = models.CharField(max_length=50) # these are arbitrary
	desc = models.CharField(max_length=500)
	private = models.BooleanField()
	meeting_id = models.CharField(max_length=25)
	agenda_items = models.ManyToManyField('AgendaItem', related_name="agenda_set", null=True, blank=True)

class AgendaItem(models.Model):
	name = models.CharField(max_length=50)
	desc = models.CharField(max_length=100) # is this needed?
	motions = models.ManyToManyField('Motion', related_name="motion_set", null=True, blank=True)

class Motion(models.Model):
	user = models.ForeignKey('Account', related_name="motion_user")
	timestamp = models.DateTimeField()
	name = models.CharField(max_length=50)
	desc = models.CharField(max_length=500)
	likes = models.IntegerField()
	dislikes = models.IntegerField()
	comments = models.ManyToManyField('Comment', related_name="comment_set", null=True, blank=True)

class Comment(models.Model):
	user = models.ForeignKey('Account', related_name="comment_user")
	timestamp = models.DateTimeField()
	text = models.CharField(max_length=500)

