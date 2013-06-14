from django import forms
from django.forms.fields import DateField
import datetime

STATUS=[('Public', 'Public'), ('Private', 'Private')]

class UserForm(forms.Form):
	username = forms.CharField()
	email = forms.EmailInput()
	password = forms.PasswordInput()
	phone = forms.NumberInput()

class MeetingForm(forms.Form):
	name = forms.CharField()
	desc = forms.CharField()