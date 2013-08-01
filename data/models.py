from django.db import models
from django.contrib.auth.models import User
from PIL import Image

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
	prof_pic = models.ImageField(upload_to='photos/accounts', blank=True, default=False)
	wphone = models.CharField(max_length=20, blank=True, null=True)
	hphone = models.CharField(max_length=20, blank=True, null=True)
	contacts = models.ManyToManyField('Contact', related_name='contacts', blank=True, null=True)
	voted_motions = models.ManyToManyField('Motion', blank=True, null=True)
	is_verified = models.BooleanField()
	verification_key = models.CharField(max_length=25)
	title = models.CharField(max_length=10) # Dr., Mr., Mrs., etc.
	organizations = models.ManyToManyField('Organization', related_name='orgs', null=True, blank=True)
	address=models.CharField(max_length=20, blank=True, null=True)
	page_id = models.CharField(max_length=21)
	bio = models.CharField(max_length=500, null=True, blank=True)
	birthdate = models.DateField(null=True, blank=True)
	notifications = models.TextField()
	display = models.CharField(max_length=500, null=True, blank=True)
	receive_emails = models.ManyToManyField('Meeting', related_name="meetings_emails", null=True, blank=True)


class Contact(models.Model):
	account = models.ForeignKey('Account', related_name='matching_account', null=True) # a contact may or may not be in the system
	# ForeignKey so multiple users can enter contact differently and link to same person
	title = models.CharField(max_length=10, null=True, blank=True)
	first_name = models.CharField(max_length=30, null=True, blank=True)
	last_name = models.CharField(max_length=30, null=True, blank=True)
	email = models.EmailField()
	wphone = models.CharField(max_length=20, blank=True, null=True)
	hphone = models.CharField(max_length=20, blank=True, null=True)
	address = models.CharField(max_length=200, blank=True, null=True)
	organizations = models.ManyToManyField('Organization', related_name='c_orgs', null=True, blank=True)

class Organization(models.Model):
	name = models.CharField(max_length=100)
	desc = models.CharField(max_length=500)
	contact = models.EmailField(null=True, blank=True)
	image = models.ImageField(upload_to='photos/orgs', blank=True, null=True)
	members = models.ManyToManyField('Account', related_name='members', null=True, blank=True)
	manager = models.ManyToManyField('Account', related_name='manager')
	page_id = models.CharField(max_length=22)
	website = models.CharField(max_length=100, blank=True, null=True)

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
	organizations = models.ManyToManyField('Organization', null=True, blank=True)
	invited = models.TextField()
	location = models.CharField(max_length=200, null=True, blank=True)
	keywords = models.CharField(max_length=200, null=True, blank=True)
	friend_invites = models.NullBooleanField(null=True)
	pending = models.TextField(null=True, blank=True)
	# things below were added to accommodate interview-style meetings 
	invitees = models.ManyToManyField('Account', related_name="a_invitees", null=True, blank=True)
	invitee = models.EmailField(null=True, blank=True)
	accepted = models.NullBooleanField(null=True)
	agreed_yet = models.NullBooleanField(null=True)
	m_type = models.CharField(max_length=10, null=True, blank=True)
	questions = models.ManyToManyField('Question', related_name="q", null=True, blank=True)
	q_start = models.DateTimeField(null=True)
	q_end = models.DateTimeField(null=True)
	q_started = models.NullBooleanField(null=True)
	q_ended = models.NullBooleanField(null=True)

# whole class added to accommodate interview-style meetings
class Question(models.Model):
	asker = models.ManyToManyField('account', related_name='a_asker', null=True, blank=True)
	timestamp = models.DateTimeField(null=True, blank=True)
	title = models.CharField(max_length=100, null=True, blank=True)
	body = models.TextField()
	answer = models.TextField(null=True)
	selected = models.NullBooleanField(null=True)

class AgendaItem(models.Model):
	class Meta:
		ordering=['-id']
	name = models.CharField(max_length=1000)
	desc = models.CharField(max_length=10000) # is this needed?
	number = models.IntegerField()
	motions = models.ManyToManyField('Motion', related_name="motion_set", null=True, blank=True)
	edited = models.BooleanField(default=False)
	edited_on = models.DateTimeField(null=True, blank=True)

class Motion(models.Model):
	class Meta:
		ordering=['-likes', 'id']
	user = models.ForeignKey('Account', related_name="motion_user")
	timestamp = models.DateTimeField()
	name = models.CharField(max_length=1000)
	desc = models.CharField(max_length=10000)
	likes = models.IntegerField()
	dislikes = models.IntegerField()
	comments = models.ManyToManyField('Comment', related_name="comment_set", null=True, blank=True)
	pastname = models.CharField(max_length=1000, blank=True)
	pastdesc = models.CharField(max_length=10000, blank=True)
	modded = models.BooleanField(default=False)
	edited = models.BooleanField(default=False)
	edited_on = models.DateTimeField(null=True, blank=True)

class Comment(models.Model):
	class Meta:
		ordering=['id']
	user = models.ForeignKey('Account', related_name="comment_user")
	timestamp = models.DateTimeField()
	text = models.CharField(max_length=10000)
	pasttext = models.CharField(max_length=10000, blank=True)
	modded = models.BooleanField()
	edited = models.BooleanField(default=False)
	edited_on = models.DateTimeField(null=True, blank=True)


