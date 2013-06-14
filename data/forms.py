from django import forms
from django.forms.fields import DateField, TimeField
from django.forms import extras
import datetime
import html5.forms.widgets as html5_widgets

STATUS=[('Public', 'Public'), ('Private', 'Private')]
valid_time_formats=['%I:%M%p']

class UserForm(forms.Form):
	username = forms.CharField(required=False)
	email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'email'}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))
	retype = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))
	phone = forms.CharField(required=False)

class MeetingForm(forms.Form):
	title = forms.CharField()
	desc = forms.CharField(widget=forms.Textarea(attrs={'rows':'4', 'cols':'40','maxlength':250}), max_length=500, required=False)
	startdate = forms.DateField(widget=html5_widgets.DateInput)
	starttime = forms.TimeField(widget=forms.TimeInput(attrs={'placeholder': '12:00AM'}), input_formats=valid_time_formats)
	enddate = forms.DateField(widget=html5_widgets.DateInput)
	endtime = forms.TimeField(widget=forms.TimeInput(attrs={'placeholder': '12:00AM'}), input_formats=valid_time_formats)
	status = forms.ChoiceField(choices=STATUS, widget=forms.RadioSelect())
