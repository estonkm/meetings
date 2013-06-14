from django import forms
from django.forms.fields import DateField
import datetime

STATUS=[('Public', 'Public'), ('Private', 'Private')]

class UserForm(forms.Form):
	username = forms.CharField()
	email = forms.EmailField()
	password = forms.PasswordInput()
	phone = forms.CharField(required=False)

class MeetingForm(forms.Form):
	name = forms.CharField()
	desc = forms.CharField(required=False)
	startdate = forms.DateField()
	starttime = forms.TimeField()
	enddate = forms.DateField()
	endtime = forms.TimeField()
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect())
