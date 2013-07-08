from django.db import models
from django.contrib.auth.models import User
import PIL

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
	past_meetings = models.ManyToManyField('Meeting', related_name="meetings_past_set", null=True, blank=True)
	join_date = models.DateField()
	prof_pic = models.ImageField(upload_to='photos', blank=True, default=False)
	phone = models.CharField(max_length=20)
	contacts = models.ManyToManyField('self', blank=True, null=True)
	voted_motions = models.ManyToManyField('Motion', blank=True, null=True)
	is_verified = models.BooleanField()
	verification_key = models.CharField(max_length=25)

class Meeting(models.Model):
	class Meta:
		ordering=['id']
	members = models.ManyToManyField('Account', related_name="members_set", null=True, blank=True)
	moderators = models.ManyToManyField('Account', related_name="mods_set", null=True, blank=True)
	hosts = models.ManyToManyField('Account', related_name="host")
	startdate = models.DateField()
	starttime = models.TimeField()
	enddate = models.DateField()
	endtime = models.TimeField()
	timezone = models.CharField(max_length=20)
	title = models.CharField(max_length=1000) # these are arbitrary
	desc = models.CharField(max_length=10000)
	private = models.BooleanField()
	meeting_id = models.CharField(max_length=15)
	agenda_items = models.ManyToManyField('AgendaItem', related_name="agenda_set", null=True, blank=True)
	started = models.BooleanField()
	ended = models.BooleanField()
	summary = models.CharField(max_length=2000, blank=True)

class AgendaItem(models.Model):
	class Meta:
		ordering=['-id']
	name = models.CharField(max_length=1000)
	desc = models.CharField(max_length=10000) # is this needed?
	number = models.IntegerField()
	motions = models.ManyToManyField('Motion', related_name="motion_set", null=True, blank=True)

class Motion(models.Model):
	class Meta:
		ordering=['-likes']
	user = models.ForeignKey('Account', related_name="motion_user")
	timestamp = models.DateTimeField()
	name = models.CharField(max_length=1000)
	desc = models.CharField(max_length=10000)
	likes = models.IntegerField()
	dislikes = models.IntegerField()
	comments = models.ManyToManyField('Comment', related_name="comment_set", null=True, blank=True)
	pastname = models.CharField(max_length=1000, blank=True)
	pastdesc = models.CharField(max_length=10000, blank=True)
	modded = models.BooleanField()

class Comment(models.Model):
	class Meta:
		ordering=['id']
	user = models.ForeignKey('Account', related_name="comment_user")
	timestamp = models.DateTimeField()
	text = models.CharField(max_length=10000)
	pasttext = models.CharField(max_length=10000, blank=True)
	modded = models.BooleanField()


