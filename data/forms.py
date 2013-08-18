from django import forms
from django.forms.fields import DateField, TimeField
from django.forms import extras
from custom_widgets import SelectTimeWidget
import datetime
import html5.forms.widgets as html5_widgets
from buildtimezones import fillTZInfo

STATUS=[('Public', 'Public'), ('Private', 'Private')]
TYPES=[('Normal', 'Normal Meeting'), ('Interview', 'Interview'), ('Chat', 'Interactive Chat')]
FI=[('Yes', 'Yes'), ('No', 'No')]
TITLES = [('Mr.', 'Mr.'), ('Mrs.', 'Mrs.'), ('Ms.', 'Ms.'), ('Dr.', 'Dr.'), ('None', 'None')]
# TIMEZONES=[('UTC/GMT-12:00', 'UTC/GMT-12:00'), ('UTC/GMT-11:00', 'UTC/GMT-11:00'),
# 			('UTC/GMT-10:00', 'UTC/GMT-10:00'), ('UTC/GMT-9:00', 'UTC/GMT-9:00'), ('PDT (UTC/GMT-8:00)', 'PDT (UTC/GMT-8:00)'),
# 			('MDT (UTC/GMT-7:00)', 'MDT (UTC/GMT-7:00)'), ('CDT (UTC/GMT-6:00)', 'CDT (UTC/GMT-6:00)'), 
# 			('EDT (UTC/GMT-5:00)', 'EDT (UTC/GMT-5:00)'), ('UTC/GMT-4:00', 'UTC/GMT-4:00'), ('UTC/GMT-3:00', 'UTC/GMT-3:00'), 
# 			('UTC/GMT-2:00', 'UTC/GMT-2:00'), ('UTC/GMT-1:00', 'UTC/GMT-1:00'), 
# 			('UTC/GMT','UTC/GMT'), 
# 			('UTC/GMT+1:00','UTC/GMT+1:00'), ('UTC/GMT+2:00','UTC/GMT+2:00'), ('EAT (UTC/GMT+3:00)', 'EAT (UTC/GMT+3:00)'),
# 			('UTC/GMT+4:00', 'UTC/GMT+4:00'), ('UTC/GMT+5:00', 'UTC/GMT+5:00'), ('UTC/GMT+6:00', 'UTC/GMT+6:00'),
# 			('UTC/GMT+7:00', 'UTC/GMT+7:00'), ('UTC/GMT+8:00', 'UTC/GMT+8:00'), ('UTC/GMT+9:00', 'UTC/GMT+9:00'),
# 			('UTC/GMT+10:00', 'UTC/GMT+10:00'), ('UTC/GMT+11:00', 'UTC/GMT+11:00'), ('UTC/GMT+12:00', 'UTC/GMT+12:00')]
valid_time_formats=['%I:%M%p']
TIMEZONES = fillTZInfo()

class UserForm(forms.Form):
	username = forms.CharField(required=False)
	first_name = forms.CharField()
	last_name = forms.CharField()
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))
	retype = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))
	phone = forms.CharField(required=False)

class ChatForm(forms.Form):
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	agreed = forms.ChoiceField(choices=FI, widget=forms.RadioSelect())
	desc = forms.CharField()

class DTInterviewForm(forms.Form):
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	agreed = forms.ChoiceField(choices=FI, widget=forms.RadioSelect())
	startdate = forms.DateField()
	starttime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False))
	enddate = forms.DateField()
	endtime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False))
	description = forms.CharField()

class InterviewForm(forms.Form):
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	agreed = forms.ChoiceField(choices=FI, widget=forms.RadioSelect())
	desc = forms.CharField()

class ContactForm(forms.Form):
	title = forms.ChoiceField(choices=TITLES, widget=forms.Select(attrs={'style':'width: 70px !important;'}), required=False)
	first_name = forms.CharField(required=False)
	last_name = forms.CharField(required=False)
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	wphone = forms.CharField(required=False)
	hphone = forms.CharField(required=False)
	address = forms.CharField(required=False)

class MeetingForm(forms.Form):
	title = forms.CharField()
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}), max_length=500)
	use_dt = forms.ChoiceField(choices=FI, widget=forms.RadioSelect())
	startdate = forms.DateField(required=False)
	starttime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False), required=False)
	enddate = forms.DateField(required=False)
	location = forms.CharField(required=False)
	endtime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False), required=False)
	timezone = forms.ChoiceField(choices=TIMEZONES, widget=forms.Select(attrs={'style':'height: 30px !important;'}))
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect())
	interview = forms.ChoiceField(choices=TYPES, widget=forms.RadioSelect())
	image = forms.ImageField(required=False)

class LoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))

class OrganizationForm(forms.Form):
	name = forms.CharField()
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}))
	image = forms.ImageField(required=False)
	contact = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	website = forms.CharField(required=False)

class OrgEmailForm(forms.Form):
	contact = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}), required=False)

class MeetingOrgForm(forms.Form):
	name = forms.CharField(required=False)
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}), required=False)
	image = forms.ImageField(required=False)
	contact = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}), required=False)
	website = forms.CharField(required=False)

class SettingsForm(forms.Form):
	title = forms.CharField(required=False)
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}), max_length=500, required=False)
	startdate = forms.DateField(required=False)
	starttime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_none=True, use_seconds=False), required=False)
	enddate = forms.DateField(required=False)
	endtime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_none=True, use_seconds=False), required=False)
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect(), required=False)
	fi = forms.ChoiceField(choices=FI, widget=forms.RadioSelect(), required=False)

class ImgForm(forms.Form):
	image = forms.ImageField(required=False)

