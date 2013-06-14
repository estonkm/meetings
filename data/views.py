# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render_to_response
from django.template import RequestContext
from django.core.context_processors import csrf
from data.forms import MeetingForm, UserForm
from data.models import Account, Meeting, AgendaItem, Motion
from django.contrib.auth.models import User
from datetime import datetime

def home(request):
	return render_to_response('index.html')

def create(request):
	context = {}
	context.update(csrf(request))
	form = MeetingForm(request.POST, request.FILES)
	context['form'] = form

	if request.method == 'POST':
		if request.POST.get('submit_request'):
			if form.is_valid():
				cd = form.cleaned_data

				print 'ok'

				#u = User.objects.get(username__exact='temp')
				#a = Account(user=u, join_date=datetime.now(), phone='eh')
				a = Account.objects.filter(phone__exact='eh')[0]

				s = True
				if cd['status'] is 'Public':
					s=False
				m = Meeting(startdate=cd['startdate'], starttime=cd['starttime'], enddate=cd['enddate'],
					endtime=cd['endtime'], title=cd['title'], desc=cd['desc'], private=s)
				m.save()
				m.hosts.add(a)
				m.save()

				return HttpResponseRedirect('../thanks')
			else:
				errors = {}
				context['errors'] = errors
				cd = form.cleaned_data
				print 'hi'

	return render_to_response('create.html', context)

def signup(request):
	context = {}
	context.update(csrf(request))
	form = UserForm(request.POST, request.FILES)
	context['form'] = form

	if request.method == 'POST':
		if request.POST.get('submit_request'):
			if form.is_valid():
				cd = form.cleaned_data

				u = User.objects.create_user(cd['email'], email=cd['email'], password=cd['password'], )
				a = Account(user=u, join_date=datetime.now(), phone="eh") #phone needs to be made non-mandatory
				a.save()

				return HttpResponseRedirect('../create/')
			else:
				errors = {}
				context['errors'] = errors
				cd = form.cleaned_data

	return render_to_response('signup.html', context)

def thanks(request):
	return render_to_response('thanks.html')

def meeting(request):
	return render_to_response('meeting_page.html')