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
	form = MeetingForm()
	context['form'] = form
	context['user'] = request.user

	if request.method == 'POST':
		form = MeetingForm(request.POST)
		if request.POST.get('submit_request'):
			if form.is_valid():
				cd = form.cleaned_data
				#u = User.objects.get(username__exact='temp')
				#a = Account(user=u, join_date=datetime.now(), phone='eh')
				#TODO: clean these hard-coded things
				a = Account.objects.get(user=request.user)

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

				counter = 1
				item_name = 'agenda_item_'+str(counter)
				while request.POST.get(item_name):
					agendaitem = request.POST.get(item_name)
					if agendaitem:
						i = AgendaItem(name=agendaitem, desc='')
						i.save()
						m.agenda_items.add(i)
						m.save()
					counter += 1
					item_name = 'agenda_item_'+str(counter)

				a.meetings_created.add(m)
				a.meetings_in.add(m)
				a.save()

				return HttpResponseRedirect('../meeting/'+meeting_no)
			else:
				errors = {}
				context['errors'] = errors
				cd = form.cleaned_data

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
					u = User.objects.create_user(cd['email'], first_name=cd['first_name'],
						last_name=cd['last_name'], email=cd['email'], password=cd['password'])
					a = Account(user=u, join_date=datetime.now(), phone='') 
					#TODO: phone needs to be made non-mandatory
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

	a = Account.objects.get(user=request.user)
	context['account'] = a
	context['meetingsin'] = a.meetings_in.order_by("id").reverse()
	context['meetingscreated'] = a.meetings_created.order_by("id").reverse()

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

	a = Account.objects.get(user=request.user)
	contacts = a.contacts.all()

	context['contacts'] = contacts

	if request.method == 'POST':
		query = request.POST.get('search')
		if query:
			u = User.objects.filter(email=query)
			if u:
				b = Account.objects.get(user=u[0])
				a.contacts.add(b)
				a.save()
				context['result'] = b.user.username + ' was successfully added to your contacts.'
				print 'hi'
			else:
				print 'hey'
				context['nosuch'] = 'No such user exists.'
			
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

	print 'hi'
	if request.method=='POST':
		print 'ok'
		motiontext = request.POST.get('motiontext')
		if motiontext:
			print "success"
			motion = Motion(user=Account.objects.get(user=request.user), timestamp=datetime.now(), name=motiontext, desc='',
				likes=0, dislikes=0)
			motion.save()

			ai_id = request.POST.get('addmotion')
			print ai_id
			modified_ai = AgendaItem.objects.get(id__exact=ai_id)
			modified_ai.motions.add(motion)
			modified_ai.save()

	context['m'] = meeting
	context['agenda_items'] = meeting.agenda_items.all()

	return render_to_response('meeting_page.html', context)




