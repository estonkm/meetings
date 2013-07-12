from django import forms
from django.forms.fields import DateField, TimeField
from django.forms import extras
from custom_widgets import SelectTimeWidget
import datetime
import html5.forms.widgets as html5_widgets

STATUS=[('Public', 'Public'), ('Private', 'Private')]
TITLES = [('Mr.', 'Mr.'), ('Mrs.', 'Mrs.'), ('Ms.', 'Ms.'), ('Dr.', 'Dr.'), ('None', 'None')]
TIMEZONES=[('UTC-12:00', 'UTC-12:00'), ('UTC-11:00', 'UTC-11:00'),
			('UTC-10:00', 'UTC-10:00'), ('UTC-9:00', 'UTC-9:00'), ('PDT (UTC-8:00)', 'PDT (UTC-8:00)'),
			('MDT (UTC-7:00)', 'MDT (UTC-7:00)'), ('CDT (UTC-6:00)', 'CDT (UTC-6:00)'), 
			('EDT (UTC-5:00)', 'EDT (UTC-5:00)'), ('UTC-4:00', 'UTC-4:00'), ('UTC-3:00', 'UTC-3:00'), 
			('UTC-2:00', 'UTC-2:00'), ('GMT (UTC-1:00)', 'GMT (UTC-1:00)'), 
			('UTC','UTC'), 
			('UTC+1:00','UTC+1:00'), ('UTC+2:00','UTC+2:00'), ('EAT (UTC+3:00)', 'EAT (UTC+3:00)'),
			('UTC+4:00', 'UTC+4:00'), ('UTC+5:00', 'UTC+5:00'), ('UTC+6:00', 'UTC+6:00'),
			('UTC+7:00', 'UTC+7:00'), ('UTC+8:00', 'UTC+8:00'), ('UTC+9:00', 'UTC+9:00'),
			('UTC+10:00', 'UTC+10:00'), ('UTC+11:00', 'UTC+11:00'), ('UTC+12:00', 'UTC+12:00')]
valid_time_formats=['%I:%M%p']

class UserForm(forms.Form):
	username = forms.CharField(required=False)
	first_name = forms.CharField()
	last_name = forms.CharField()
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))
	retype = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))
	phone = forms.CharField(required=False)

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
	startdate = forms.DateField()
	starttime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False))
	enddate = forms.DateField()
	endtime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False))
	timezone = forms.ChoiceField(choices=TIMEZONES)
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect())

class LoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))

class OrganizationForm(forms.Form):
	name = forms.CharField()
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}))
	image = forms.ImageField(required=False)
	contact = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))

class MeetingOrgForm(forms.Form):
	name = forms.CharField(required=False)
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}), required=False)
	image = forms.ImageField(required=False)
	contact = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}), required=False)

class SettingsForm(forms.Form):
	title = forms.CharField(required=False)
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}), max_length=500, required=False)
	startdate = forms.DateField(required=False)
	starttime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False), required=False)
	enddate = forms.DateField(required=False)
	endtime = forms.TimeField(widget=SelectTimeWidget(twelve_hr=True, use_seconds=False), required=False)
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect(), required=False)

class ImgForm(forms.Form):
	image = forms.ImageField()

