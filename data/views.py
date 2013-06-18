# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render_to_response
from django.template import RequestContext
from django.core.context_processors import csrf
from data.forms import MeetingForm, UserForm
from data.models import Account, Meeting, AgendaItem, Motion
from django.contrib.auth.models import User
from datetime import datetime
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
import random
from django.core.urlresolvers import resolve

def index(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user
	
	if request.method == 'POST':
		user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
		if user is None:
			print "Invalid login credentials"
			# set form errors
			context['errors'] = True
			return render_to_response('login.html', context)
		else:
			auth_login(request, user)
			# sets session; redirect to home page for user
			return HttpResponseRedirect('../home/')

	return render_to_response('index.html', context)

def create(request):
	context = {}
	context.update(csrf(request))
	form = MeetingForm(request.POST, request.FILES)
	context['form'] = form
	context['user'] = request.user

	if request.method == 'POST':
		if request.POST.get('submit_request'):
			if form.is_valid():
				cd = form.cleaned_data

				print 'ok'

				#u = User.objects.get(username__exact='temp')
				#a = Account(user=u, join_date=datetime.now(), phone='eh')
				#TODO: clean these hard-coded things
				a = Account.objects.filter(phone__exact='eh')[0]

				s = True
				if cd['status'] is 'Public':
					s=False

				random.seed()

				meeting_no = ''
				for i in range(25):
					# TODO: add upper/lower case letters as well for extra protection
					meeting_no += str(int(random.random()*10))

				m = Meeting(startdate=cd['startdate'], starttime=cd['starttime'], enddate=cd['enddate'],
					endtime=cd['endtime'], title=cd['title'], desc=cd['desc'], private=s, meeting_id=meeting_no)
				m.save()
				m.hosts.add(a)
				m.save()

				a.meetings_created.add(m)
				a.meetings_in.add(m)
				a.save()

				print 'id: ' + meeting_no

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

				if User.objects.filter(username=cd['email']) or User.objects.filter(email=cd['email']):
					context['email_taken'] = True
				else:
					u = User.objects.create_user(cd['email'], email=cd['email'], password=cd['password'], )
					a = Account(user=u, join_date=datetime.now(), phone="eh") #phone needs to be made non-mandatory
					a.save()
					print 'success'

					return HttpResponseRedirect('../create/')
			else:
				errors = {}
				context['errors'] = errors
				cd = form.cleaned_data

	return render_to_response('signup.html', context)

def login(request):
	context = {}
	context.update(csrf(request))

	if request.method == 'POST':
		if request.POST.get('submit_request'):
			user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
			if user is None:
				print "Invalid login credentials"  
				# set form errors
				context['errors'] = True
			else:
				auth_login(request, user)
				# sets session; redirect to home page for user
				return HttpResponseRedirect('../home/')

	return render_to_response('login.html', context)

def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('../')

def home(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	return render_to_response('home.html', context)

def profile(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	return render_to_response('profile.html', context)

def contacts(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	return render_to_response('contacts.html', context)

def thanks(request):
	return render_to_response('thanks.html')

def meeting(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	path = ''
	if 'meeting' in request.path:
		path = request.path.split('/')[2]

	meeting = Meeting.objects.filter(meeting_id__exact=path)
	if meeting:
		meeting = meeting[0]
	else:
		return render_to_response('error.html')

	context['m'] = meeting

	return render_to_response('meeting_page.html', context)




