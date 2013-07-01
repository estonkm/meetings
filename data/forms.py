from django import forms
from django.forms.fields import DateField, TimeField
from django.forms import extras
import datetime
import html5.forms.widgets as html5_widgets

STATUS=[('Public', 'Public'), ('Private', 'Private')]
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

class MeetingForm(forms.Form):
	title = forms.CharField()
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}), max_length=500)
	startdate = forms.DateField()
	starttime = forms.TimeField(widget=forms.TimeInput(attrs={'placeholder': '12:00AM'}), input_formats=valid_time_formats)
	enddate = forms.DateField()
	endtime = forms.TimeField(widget=forms.TimeInput(attrs={'placeholder': '12:00AM'}), input_formats=valid_time_formats)
	timezone = forms.ChoiceField(choices=TIMEZONES)
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect())

class LoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))

class SettingsForm(forms.Form):
	title = forms.CharField(required=False)
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'3', 'cols':'40','maxlength':250}), max_length=500, required=False)
	startdate = forms.DateField(widget=html5_widgets.DateInput, required=False)
	starttime = forms.TimeField(widget=forms.TimeInput(attrs={'placeholder': '12:00AM'}), input_formats=valid_time_formats, required=False)
	enddate = forms.DateField(widget=html5_widgets.DateInput, required=False)
	endtime = forms.TimeField(widget=forms.TimeInput(attrs={'placeholder': '12:00AM'}), input_formats=valid_time_formats, required=False)
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect(), required=False)

