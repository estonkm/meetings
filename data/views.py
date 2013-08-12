# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render_to_response
from django.template import RequestContext
from django.core.context_processors import csrf
from data.forms import *
from data.models import *
from django.contrib.auth.models import User
from datetime import datetime, date
import time
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
import random
from django.core.urlresolvers import resolve
from django.core import serializers
from django.utils import simplejson
import re, os
from django.core.mail import send_mail
from django.conf import settings as dsettings
from PIL import Image, ImageOps
from pytz import timezone
import pytz
from django.utils.timezone import activate
#import requests

SENDER = 'Vital Meeting <info@vitalmeeting.com>'
SIGNATURE = '\n\n\n\nVitalMeeting.com\nStructured Online Meetings'
UTC = pytz.utc
ZONE = timezone('America/Chicago')

EMAILS_ENABLED = True

#------------------- HELPER FUNCTIONS ----------------------------------------#

# not used
def check_img_size(img):
	# 2.5MB = 2621440
	MAX_SIZE = "2621440"
	if img._size > MAX_SIZE:
		return False
	else:
		return True

# used
def send_email_invite(meeting, user, recipients):
		title = "Meeting Invite: " + meeting.title
		items = meeting.agenda_items.all().order_by('id')
		org = meeting.organizations.all()
		org_details = ''
		if org:
			org = org[0]
			org_details = ', which is sponsored by '+org.name+','
		ai_details = ''
		if items:
			ai_details += 'Agenda Items:\n'
		if meeting.m_type=="Interview":
			if meeting.invitee in recipients:
				recipients.remove(meeting.invitee)
		for i in range(len(items)):
			ai_details += str(i+1)+'. '+ items[i].name + '\n'
		message = ("You've been invited to attend " + user.first_name + " " + user.last_name + "'s online meeting" + org_details +
					" on VitalMeeting.com.\n\n"+ai_details+"\n\nPlease click on " +
					"http://vitalmeeting.com/meeting/"+meeting.meeting_id+" to join in."+SIGNATURE)
		if EMAILS_ENABLED:
			send_mail(title, message, SENDER, recipients)

# used 

# handles the input from the external address book;
# "remember" is optional parameter--to save these contacts into the
# account's contacts
# returns the valid emails in a list
def handle_addr_book(account, meeting, added, save):
	added = added.split(',')
	recipients = []
	for contact in added:
		c_email = re.findall('[\S]*@[\S]*\.[\S]*', contact)
		if c_email:
			c_email = c_email[0].strip('<>')
			recipients.append(c_email)

			if meeting:
				meeting.invited += c_email + ','

			contact = contact.strip(' ')
			contact_info = contact.split(' ')
			c_first_name = ''
			c_last_name = ''
			if len(contact_info) > 2:
				c_first_name = contact_info[0]
				c_last_name = contact_info[1]
			match = Contact.objects.filter(email=c_email)
			u = User.objects.filter(email=c_email)

			if u and meeting:
				a = Account.objects.filter(user=u[0])
				if a:
					a = a[0]
					a.meetings_in.add(meeting)
					meeting.members.add(a)
					a.save()
			if save:
				if match:
					if match not in account.contacts.all():
						account.contacts.add(match[0])
						account.save()
				else:
					new_c = Contact(first_name=c_first_name, last_name=c_last_name, email=c_email)
					new_c.save()
					account.contacts.add(new_c)
					account.save()	
	return recipients

# not used
def mailgun_send(recipients, subject, message):
	return requests.post(
		"https://api.mailgun.net/v2/rs3945.mailgun.org/messages",
		auth=("api", "key-6jh7x-u493r23q8bi-cgkntmlcbc7pd1"),
		data={"from": "VitalMeeting <updates@rs3945.mailgun.org>",
				"to": recipients,
				"subject": subject,
				"text": message})

#----------------------------------------------------------------------------#

def index(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user
	
	if request.method == 'POST':
		user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
		if user is None:

			# set form errors
			context['errors'] = True
			return render_to_response('login.html', context)
		else:
			a = Account.objects.filter(user=user)
			if a:
				if not a[0].is_verified:
					context['not_verified'] = True
					return render_to_response('login.html', context)
			auth_login(request, user)
			# sets session; redirect to home page for user
			return HttpResponseRedirect('../home/')

	return render_to_response('index.html', context)

def setinterview(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if not request.user.is_authenticated() and not 'account' in request.session:
		return HttpResponseRedirect('/')

	if not 'account' in request.session:
		a = Account.objects.get(user=request.user)
	else:
		a = request.session['account']

	context['orgs'] = a.organizations.all()

	m = Meeting.objects.filter(meeting_id__exact=request.session['meeting_created'])
	if m:
		m = m[0]
	else:
		return HttpResponseRedirect('/')

	if m.uses_dt:
		context['uses_dt'] = True
		form = DTInterviewForm()
	else:
		context['uses_dt'] = False
		form = InterviewForm()

	if request.method == 'POST':
		if m.uses_dt:
			form = DTInterviewForm(request.POST)
		else:
			form = InterviewForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data

			m.invitee = cd['email']
			m.invited = cd['email'] + ','

			meetingtz = timezone(m.timezone)

			if m.uses_dt:
				enteredtimestart = datetime.combine(cd['startdate'], cd['starttime'])
				enteredtimeend = datetime.combine(cd['enddate'], cd['endtime'])
				
				if (enteredtimestart-enteredtimeend).total_seconds() > 0:
					context['time_mismatch'] = True
					context['form'] = form
					return render_to_response('setinterview.html', context)
				
				m.q_start = meetingtz.localize(enteredtimestart)
				m.q_end = meetingtz.localize(enteredtimeend)

			if cd['agreed'] == 'Yes':
				m.accepted = True
				m.agreed_yet = True
			else:
				m.agreed_yet = False
				host = m.hosts.all()[0]
				message = (host.user.first_name+' '+host.user.last_name+
					' would like you to be the subject in the interview "'+m.title+'".\n\n'+
					'The description is: '+m.desc+'\n\n'+
					'Please go to http://vitalmeeting.com/meeting/'+m.meeting_id+' to see the details, and to accept or'+
					' reject this request.'+SIGNATURE)
				title = "Interview Invite: "+m.title
				if EMAILS_ENABLED:
					send_mail(title, message, SENDER, [m.invitee])

			m.save()

			return HttpResponseRedirect('../attachorg', context)
		else:
			errors = {}
			context['errors'] = errors

	context['form'] = form

	return render_to_response('setinterview.html', context)

def setchat(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user
	form = ChatForm()

	if not request.user.is_authenticated() and not 'account' in request.session:
		return HttpResponseRedirect('/')

	if not 'account' in request.session:
		a = Account.objects.get(user=request.user)
	else:
		a = request.session['account']

	m = Meeting.objects.filter(meeting_id__exact=request.session['meeting_created'])
	if m:
		m = m[0]
	else:
		return HttpResponseRedirect('/')

	if request.method == 'POST':
		form = ChatForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data

			m.invitee = cd['email']
			m.invited = cd['email'] + ','

			if cd['agreed'] == 'Yes':
				m.accepted = True
				m.agreed_yet = True
			else:
				m.agreed_yet = False
				host = m.hosts.all()[0]
				message = (host.user.first_name+' '+host.user.last_name+
					' would like you to be the subject in the interactive chat "'+m.title+'".\n\n'+
					'The description is: '+m.desc+'\n\n'+
					'Please go to http://vitalmeeting.com/meeting/'+m.meeting_id+' to see the details, and to accept or'+
					' reject this request.'+SIGNATURE)
				title = "Interview Invite: "+m.title
				if EMAILS_ENABLED:
					send_mail(title, message, SENDER, [m.invitee])

			c = Chat(chatlog='')
			c.save()
			m.chat = c

			m.save()

			return HttpResponseRedirect('../attachorg')
		else:
			errors = {}
			context['errors'] = errors

	context['form'] = form

	return render_to_response('setchat.html', context)

def setnormal(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if not request.user.is_authenticated() and not 'account' in request.session:
		request.session['fromcreate'] = True
		request.session.modified = True
		return HttpResponseRedirect('../signup/')

	if not 'account' in request.session:
		context['user'] = request.user
		a = Account.objects.get(user=request.user)
	else:
		a = request.session['account']

	m = Meeting.objects.filter(meeting_id__exact=request.session['meeting_created'])
	if m:
		m = m[0]
	else:
		return HttpResponseRedirect('/')

	if request.method=='POST':
		counter = 1
		item_name = 'agenda_item_'+str(counter)
		while request.POST.get(item_name):
			agendaitem = request.POST.get(item_name)
			if agendaitem:
				i = AgendaItem(name=agendaitem, desc='', number=counter)
				i.save()
				m.agenda_items.add(i)
				m.save()
			counter += 1
			item_name = 'agenda_item_'+str(counter)

		return HttpResponseRedirect('../attachorg/')

	return render_to_response('setnormal.html', context)


def create(request):
	context = {}
	context.update(csrf(request))
	form = MeetingForm()
	context['user'] = request.user

	if not request.user.is_authenticated() and not 'account' in request.session:
		request.session['fromcreate'] = True
		request.session.modified = True
		return HttpResponseRedirect('../signup/')

	if not 'account' in request.session:
		context['user'] = request.user
		a = Account.objects.get(user=request.user)
	else:
		a = request.session['account']

	if request.method == 'POST':
		form = MeetingForm(request.POST)
		if request.POST.get('submit_request'):
			if form.is_valid():
				cd = form.cleaned_data

				if cd['use_dt'] == 'Yes':
					use_dt = True
				else:
					use_dt = False

				dt_error = False

				if use_dt:
					if not startdate:
						context['nostartdate'] = True
						dt_error = True
					if not starttime:
						context['nostarttime'] = True
						dt_error = True
					if not enddate:
						context['noenddate'] = True
						dt_error = True
					if not endtime:
						context['noendtime'] = True
						dt_error = True
					if dt_error:
						context['dterrors'] = True

				if not dt_error:
					s = True
					if cd['status'] == 'Public':
						s=False

					fi = True
					if s:
						fi = False

					tz = cd['timezone']
					meetingtz = timezone(tz)

					random.seed()

					meeting_no = ''
					for i in range(15):
						# TODO: add upper/lower case letters as well for extra protection
						meeting_no += chr(int(random.random()*25)+97)

					# these should hopefully return timedeltas and work
					q_status = False

					if use_dt:
						already_started = False
						already_ended = False

						enteredtimestart = datetime.combine(cd['startdate'], cd['starttime'])
						enteredtimeend = datetime.combine(cd['enddate'], cd['endtime'])
					
						enteredtimestart = meetingtz.localize(enteredtimestart)
						enteredtimeend = meetingtz.localize(enteredtimeend)

						rightnow = (ZONE.localize(datetime.now())).astimezone(meetingtz)

						if (rightnow-enteredtimestart).total_seconds() > 0:
							already_started = True
						if (rightnow-enteredtimeend).total_seconds() > 0:
							already_ended = True

						if (enteredtimestart-enteredtimeend).total_seconds() > 0:
							context['time_mismatch'] = True
							context['form'] = form
							return render_to_response('create.html', context)
					else:
						already_started = True
						already_ended = False
						q_status = True

					# check if question period started yet--report error

					m = Meeting(startdate=cd['startdate'], starttime=cd['starttime'], enddate=cd['enddate'],
						endtime=cd['endtime'], title=cd['title'], desc=cd['desc'], private=s, meeting_id=meeting_no, 
						started=already_started, ended=already_ended, timezone=cd['timezone'], m_type=cd['interview'], 
						q_started=q_status, q_ended=False, uses_dt=use_dt, friend_invites=fi)
					m.save()
					m.hosts.add(a)
					m.members.add(a)
					m.save()

					a.meetings_created.add(m)
					a.meetings_in.add(m)
					a.save()

					request.session['meeting_created'] = meeting_no
					request.session.modified=True

					if m.m_type == 'Interview':
						return HttpResponseRedirect('../setinterview/')
					elif m.m_type == 'Chat':
						return HttpResponseRedirect('../setchat/')
					else:
						return HttpResponseRedirect('../setnormal/')
			else:
				errors = {}
				context['errors'] = errors

	context['form'] = form

	return render_to_response('create.html', context)

def invite(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if not request.user.is_authenticated() and not 'account' in request.session:
		return HttpResponseRedirect('../signup/')

	if not 'account' in request.session:
		a = Account.objects.get(user=request.user)
	else:
		a = request.session['account']

	context['account'] = a

	meeting_no = request.session['meeting_created']

	meeting = Meeting.objects.get(meeting_id__exact=meeting_no)
	context['meeting'] = meeting

	remember = False
	invite_later = False

	if request.method=='POST':
		if 'remember' in request.POST:
			remember = True

		if 'allow_fi' in request.POST:
			meeting.friend_invites = True
		meeting.save()

		if "later" in request.POST:
			return HttpResponseRedirect('../meeting/'+meeting_no)

		if "invite_later" in request.POST:
			invite_later = True

		added = request.POST.get('from_contacts')
		entered = request.POST.get('entered')

		recipients = []

		if added:
			added = added.split(' ')
			for c_id in added:
				if c_id != '':
					contact = a.contacts.filter(id__exact=c_id)
					if contact:
						contact = contact[0]
						meeting.invited += contact.email + ','
						meeting.save()

						recipients.append(contact.email)


		if request.POST.get('entered'):
			entered = request.POST.get('entered').split('\n')

			for e in entered:
				e = e.strip('\r')
				meeting.invited += e + ','
				match = Contact.objects.filter(email=e)
				if remember:
					if match:
						if match not in a.contacts.all():
							a.contacts.add(match[0])
							a.save()
					else:
						new_c = Contact(email=e)
						new_c.save()
						a.contacts.add(new_c)
						a.save()
				meeting.save()
				recipients.append(e)

		if request.POST.get('addr_contacts'):
			added = request.POST.get('addr_contacts')
			# just copied code over to "handle_addr_book": if something breaks,
			# add it back
			addr_book_cs = handle_addr_book(a, meeting, added, remember)
			recipients += addr_book_cs
			for c in addr_book_cs:
				meeting.invited += c + ','
			meeting.save()

		if (meeting.m_type == 'Interview' and not meeting.accepted):
			invite_later = True

		if recipients and not invite_later:
			send_email_invite(meeting, a.user, recipients)

		if invite_later:
			meeting.pending = meeting.invited
			meeting.save()

		if 'account' in request.session:
			del request.session['account']

		request.session.modified = True
		return HttpResponseRedirect('../meeting/'+meeting_no)

	return render_to_response('invite.html', context)

def signup(request):
	context = {}
	context.update(csrf(request))
	form = UserForm()

	if request.user.is_authenticated():
		return HttpResponseRedirect('../home/')

	if request.method == 'POST':
		form = UserForm(request.POST, request.FILES)
		if request.POST.get('submit_request'):
			if form.is_valid():
				cd = form.cleaned_data

				if User.objects.filter(username=cd['email']) or User.objects.filter(email=cd['email']):
					context['email_taken'] = True
				elif len(cd['password']) < 8:
					context['too_short'] = True
				elif cd['password'] != cd['retype']:
					context['retype_failed'] = True
				else:
					vkey = ''
					pid = ''

					random.seed()

					for i in range(25):
						vkey += chr(int(random.random()*25)+97)

					for i in range(21):
						pid += chr(int(random.random()*25)+97)

					u = User.objects.create_user(cd['email'], first_name=cd['first_name'],
						last_name=cd['last_name'], email=cd['email'], password=cd['password'])
					a = Account(user=u, join_date=ZONE.localize(datetime.now()), is_verified=False, verification_key=vkey, page_id=pid) 
					a.save()

					for m in Meeting.objects.all():
						if u.email in m.invited:
							a.meetings_in.add(m)
							m.members.add(a)
							m.save()
					a.save()


					for c in Contact.objects.all():
						if c.email == u.email:
							c.account = a
							c.first_name = u.first_name
							c.last_name = u.last_name
							c.save()
							break

					# TODO - use verification and don't log on just yet
					recipient = [u.email]
					message = 'Please go to http://vitalmeeting.com/verify/'+vkey+' to verify your account. Thanks!\n\n\n\nVitalMeeting.com\nStructured Online Meetings'
					if EMAILS_ENABLED:
						send_mail('Account Verification', message, SENDER, recipient)

					#user = authenticate(username=cd['email'], password=cd['password'])
					#auth_login(request, user)
					context['success'] = True

					if 'fromcreate' in request.session:
						#return HttpResponseRedirect('../create/')
						context['destination'] = '../create/'
						request.session['account'] = a
						request.session.modified = True
					else:
						#return HttpResponseRedirect('../home/')
						context['destination'] = '../home/'

			else:
				errors = {}
				context['errors'] = errors

	context['form'] = form
	if 'fromcreate' in request.session:
		context['fromcreate'] = True

	return render_to_response('signup.html', context)

def verify(request):
	context = {}
	context.update(csrf(request))

	if request.user.is_authenticated():
		return HttpResponseRedirect('../home/')
	else:
		path = ''
		if 'verify' in request.path:
			path = request.path.split('/')[2]
		else:
			return HttpResponseRedirect('..')

		a = Account.objects.filter(verification_key__exact=path)
		if not a:
			return HttpResponseRedirect('..')
		elif a[0].is_verified:
			return HttpResponseRedirect('../home/')
		else:
			user = a[0].user
			a[0].is_verified = True
			a[0].save()
			# the password is hashed before it is stored, so you can't retrieve it and use it
			user.backend = 'django.contrib.auth.backends.ModelBackend'
			auth_login(request, user)

			if 'meeting_created' in request.session:
				context['meeting'] = request.session['meeting_created']
			return render_to_response('verify.html', context)

def login(request):
	context = {}
	context.update(csrf(request))

	if request.user.is_authenticated():
		return HttpResponseRedirect('../home/')

	if request.method == 'POST':
		if request.POST.get('submit_request'):
			user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
			if user is None:
				# set form errors
				context['errors'] = True
			else:
				a = Account.objects.filter(user=user)
				if a:
					if not a[0].is_verified:
						context['not_verified'] = True
						return render_to_response('login.html', context)
				auth_login(request, user)
				# sets session; redirect to home page for user
				return HttpResponseRedirect('../home/')

	return render_to_response('login.html', context)

def logout(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('../signup/')
	auth_logout(request)
	return HttpResponseRedirect('../')

def home(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	a = Account.objects.get(user=request.user)
	context['account'] = a
	context['meetingsin'] = a.meetings_in.order_by("id").reverse()
	context['meetingscreated'] = a.meetings_created.order_by("id").reverse()
	context['meetingspast'] = a.past_meetings.order_by("id").reverse()
	context['organizations'] = a.organizations.all()

	return render_to_response('home.html', context)

def profile(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	form = ImgForm()
	context['form'] = form

	account = Account.objects.get(user=request.user)
	context['account'] = account

	if request.POST:
		if 'pic' in request.POST:
			form = ImgForm(request.POST, request.FILES)
			if form.is_valid():
				cd = form.cleaned_data
				account.prof_pic = cd['image']
				account.save()

				if cd['image'] is not None:
					path = os.path.join(dsettings.MEDIA_ROOT, account.prof_pic.url)
					tn= Image.open(path)
					tn.thumbnail((200, 200), Image.ANTIALIAS)
					tn.save(path)

		if 'bio' in request.POST:
			account.bio = request.POST.get('bio')
			account.save()

		if 'wphone' in request.POST:
			wphone = request.POST.get('wphone')
			wphone = re.sub('[- ()]', '', wphone)
			if re.match("^\+?[0-9]*$", wphone):
				account.wphone = wphone
				account.save()
			else:
				context['wphone_errors'] = True

		if 'hphone' in request.POST:
			hphone = request.POST.get('hphone')
			hphone = re.sub('[- ()]', '', hphone)
			if re.match("^\+?[0-9]*$", hphone):
				account.hphone = hphone
				account.save()
			else:
				context['hphone_errors'] = True

	return render_to_response('profile.html', context)

def contacts(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user
	form = ContactForm()

	a = Account.objects.get(user=request.user)
	contacts = a.contacts.all()

	context['meetings'] = a.meetings_in.all()
	context['account'] = a

	if request.method == 'POST':
		if 'new_contact' in request.POST:
			form = ContactForm(request.POST)
			if form.is_valid():
				cd = form.cleaned_data
				in_contacts = False
				for c in contacts:
					if c.email == cd['email']:
						in_contacts = True
				if in_contacts:
					context['in_contacts'] = True
				else:
					u = User.objects.filter(email__exact=cd['email'])
					matching_account = None
					if u:
						matching_account = Account.objects.get(user=u)
					c = Contact(first_name=cd['first_name'], last_name=cd['last_name'],
							email=cd['email'], address=cd['address'], wphone=cd['wphone'], hphone=cd['hphone'])
					if matching_account:
						c.account = matching_account
					c.save()
					a.contacts.add(c)
					a.save()
			else:
				errors = {}
				context['errors'] = errors

		if request.POST.get('remove_contact'):
			cid = request.POST.get('remove_contact')
			contact = Contact.objects.get(id__exact=cid)
			a.contacts.remove(contact)
			a.save()

		if 'addr_contacts' in request.POST:
			added = request.POST.get('addr_contacts')
			handle_addr_book(a, None, added, True)
	
	contacts = a.contacts.all().order_by('first_name')
	contacts = contacts.order_by('last_name')
	context['contacts'] = contacts
	context['form'] = form

	return render_to_response('contacts.html', context)

def addorganizer(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	context = {}
	context.update(csrf(request))
	form = OrganizationForm()
	context['user'] = request.user

	a = Account.objects.get(user=request.user)

	if 'submit_request' in request.POST:
		form = OrganizationForm(request.POST, request.FILES)
		if form.is_valid():
			cd = form.cleaned_data;
			random.seed()

			pid = ''
			for i in range(22):
				# TODO: add upper/lower case letters as well for extra protection
				pid += chr(int(random.random()*25)+97)

			o = Organization(name=cd['name'], desc=cd['desc'], image=cd['image'], contact=cd['contact'], website=cd['website'], page_id=pid)
			o.save()
			o.manager.add(a)
			o.save()
			a.organizations.add(o)
			a.save()

			if cd['image'] is not None:
				path = os.path.join(dsettings.MEDIA_ROOT, o.image.url)
				tn= Image.open(path)
				tn.thumbnail((200, 200), Image.ANTIALIAS)
				tn.save(path)
            
			return HttpResponseRedirect('../home/')

		else:
			errors = {}
			context['errors'] = errors

	context['form'] = form
	return render_to_response('addorganizer.html', context)

def vote(request):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	account = Account.objects.get(user=request.user) 
	reqfields = request.GET['val'].split('_')

	vote_type = reqfields[2]
	motion = Motion.objects.get(id__exact=reqfields[1])

	if account.voted_motions.filter(id__exact=reqfields[1]):
		return HttpResponse('["failure"]', content_type="application/json")

	account.voted_motions.add(motion)

	if vote_type == 'up':
		motion.likes += 1
	else:
		motion.dislikes += 1

	motion.save()

	return HttpResponse('[]', content_type="application/json")

def intersub(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	account = Account.objects.filter(user=request.user)
	if account:
		account = account[0]
	else:
		return HttpResponseRedirect('/')


	if request.method=='POST':
		meeting = Meeting.objects.filter(id__exact=request.POST['meeting'])
		if meeting:
			meeting = meeting[0]
		else:
			return HttpResponseRedirect('/')

		if (not meeting.started or meeting.ended) and account != meeting.hosts.all()[0]:
			return HttpResponse()\

		if account in meeting.chat.banlist.all():
			return HttpResponseRedirect('/')

		chat = meeting.chat

		if chat.chatlog is None:
			chat.chatlog = ''

		try:
			meetingtz = timezone(meeting.timezone)
		except:
			meetingtz = UTC

		dtnow = (ZONE.localize(datetime.now())).astimezone(meetingtz)
		time = dtnow.strftime("%H:%M:%S")

		if account.user.email == meeting.invitee:
			name = '<text style="color: red; font-weight: bold;">'+account.user.first_name+' '+account.user.last_name+'</text>'
		elif account in meeting.hosts.all():
			name = '<text style="color: blue; font-weight: bold;">'+account.user.first_name+' '+account.user.last_name+'</text>'
		else:
			name = '<b>'+account.user.first_name+' '+account.user.last_name+"</b>"

		cleanedtext = re.sub('[<>]', '', request.POST['text'])

		if len(cleanedtext) <= 200:
			chat.chatlog += "<div class='msgln'>("+time+") "+name+": "+cleanedtext+"<br></div>"
			chat.save()

		return HttpResponse()
	else:
		meeting = Meeting.objects.filter(id__exact=request.GET['meeting'])
		if meeting:
			meeting = meeting[0]
		else:
			return HttpResponseRedirect('/')
		return HttpResponse(meeting.chat.chatlog)

def chatonline(request):
	account = None
	if request.method=='POST':
		user = User.objects.filter(id__exact=request.POST['user'])
		if user:
			account = Account.objects.filter(user=user)
			if account:
				account = account[0]
		meeting = Meeting.objects.filter(id__exact=request.POST['meeting'])
		if meeting and account:
			meeting = meeting[0]
			meeting.chat.online.remove(account)
			meeting.chat.save()
	else:
		user = User.objects.filter(id__exact=request.GET['user'])
		if user:
			account = Account.objects.filter(user=user)
		meeting = Meeting.objects.filter(id__exact=request.GET['meeting'])
		if meeting:
			meeting = meeting[0]
			memset = []
			length = len(meeting.chat.online.all())
			for member in meeting.chat.online.all():
				memset.append(member)
			data = '['+str(length)+', "<div class=\'innerCheckbox\'>'

			for member in memset:
				data += '<div class=\'cboxContact\' style=\'height: 55px; line-height: 55px;\'>'
				if member.prof_pic != False and member.prof_pic.url != '../media/False':
					data += '<img src=\''+member.prof_pic.url+'\' style=\'width: 50px; height: auto;\'>'
				data += '<span style=\'margin-left: 10px;\'>'
				ln = member.user.last_name
				fn = member.user.first_name
				em = member.user.email
				if ln and fn:
					data += ''+ln+', '+fn+''+' <<em>'+em+'</em>>'
				elif ln:
					data += ''+ln+' <<em>'+em+'</em>>'
				elif fn:
					data += ''+fn+' <<em>'+em+'</em>>'
				else:
					data += ''+em+''
				data += '</span></div>'

			data += '</div>"]'
			return HttpResponse(data, content_type="application/json")

def chatbanlist(request):
	if request.method=='GET':
		if request.user.is_authenticated():
			account = Account.objects.filter(user=request.user)
			if account:
				account = account[0]
				meeting = Meeting.objects.filter(id__exact=request.GET['meeting'])
				if meeting:
					meeting = meeting[0]
					if account in meeting.moderators.all() or account==meeting.hosts.all()[0]:
						data = '["<div class=\'innerCheckbox\'>'
						for member in meeting.members.all():
							if (member not in meeting.moderators.all() and member!=meeting.hosts.all()[0]) and member.user.email != meeting.invitee:
								data += '<div class=\'cboxContact\'>'
								if member in meeting.chat.banlist.all():
									data += '<input type=\'checkbox\' name=\'unban_select\' value=\''+str(member.id)+'\'><text style=\'color:blue;\'> Un-ban</text></input><span style=\'margin-left: 10px;\'>'
								else:
									data += '<input type=\'checkbox\' name=\'ban_select\' value=\''+str(member.id)+'\'><text style=\'color:red;\'> Ban</text></input><span style=\'margin-left: 10px;\'>'
								data += '<span style=\'margin-left: 10px;\'>'
								ln = member.user.last_name
								fn = member.user.first_name
								em = member.user.email
								if ln and fn:
									data += ''+ln+', '+fn+''+' <<em>'+em+'</em>>'
								elif ln:
									data += ''+ln+' <<em>'+em+'</em>>'
								elif fn:
									data += ''+fn+' <<em>'+em+'</em>>'
								else:
									data += ''+em+''
								data += '</span></div>'

						data += '</div>"]'
						return HttpResponse(data, content_type="application/json")
	return HttpResponse()

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
		return HttpResponseRedirect('/')

	context['access'] = True # can the viewer view the page?
	context['not_verified'] = False # is the viewer's account verified (separate login error)
	context['login_errors'] = False # did the viewer try to log in with invalid credentials?
	context['notifications_modified'] = False # did the viewer modify email notification status?
	# ^ actually this needs to be changed yo
	context['canmod'] = False # does the viewer have moderator permissions?
	context['joined'] = False # is the viewer a member of the meeting? (permission to post/etc.)

	host = meeting.hosts.all()[0]

	try:
		meetingtz = timezone(meeting.timezone)
	except:
		meetingtz = UTC

	activate(meetingtz)

	dtnow = (ZONE.localize(datetime.now())).astimezone(UTC)

	closed = (not meeting.started or meeting.ended)

	viewer = None

	if request.user.is_authenticated():
		viewer = Account.objects.get(user=request.user)
		if viewer.user.email in meeting.invited:
			if viewer in meeting.members.all():
				context['joined'] = True
		if viewer == host:
			context['canmod'] = True
			if meeting.pending:
				context['pending'] = True
			else:
				context['pending'] = False
		elif viewer in meeting.moderators.all():
			context['canmod'] = True

		if meeting in viewer.receive_emails.all():
			context['currently_receiving'] = True 
		else:
			context['currently_receiving'] = False


	if meeting.private:
		if not request.user.is_authenticated():
			context['access'] = False
			context['not_authenticated'] = True
		elif request.user.email not in meeting.invited and viewer != host:
			context['access'] = False
			context['not_invited'] = True
			return HttpResponseRedirect('/')

	# POST requests common to all meeting types
	if request.method=='POST':
		if 'login' in request.POST:
			user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
			if user is None:
				# set form errors
				context['login_errors'] = True
			else:
				a = Account.objects.filter(user=user)
				if a:
					if not a[0].is_verified:
						context['not_verified'] = True
					else:
						auth_login(request, user)
						context['user'] = request.user
						if (request.user.email not in meeting.invited) and meeting.private:
							return HttpResponseRedirect('/')
						else:
							context['access'] = True
							context['not_authenticated'] = False
							return HttpResponseRedirect('../meeting/'+meeting.meeting_id)
		elif closed and request.user != host.user:
			context['closed_error'] = True
		else:
			if 'get_emails' in request.POST and viewer:
				viewer.receive_emails.add(meeting)
				viewer.save()
				context['receiving'] = True
				context['notifications_modified'] = True
				context['currently_receiving'] = True
			if 'stop_emails' in request.POST and viewer:
				if meeting in viewer.receive_emails.all():
					viewer.receive_emails.remove(meeting)
					viewer.save()
				context['notifications_modified'] = True
				context['receiving'] = False
				context['currently_receiving'] = False

			if 'send_pending' in request.POST and viewer:
				if viewer == meeting.hosts.all()[0]:
					recipients = []
					emails = meeting.pending.split(',')
					for e in emails:
						if '@' in e:
							recipients.append(e)
					if recipients:
						send_email_invite(meeting, viewer.user, recipients)
					meeting.pending = ''
					meeting.save()
					context['just_sent'] = True

			if request.POST.get('addr_contacts') and viewer:
				added = request.POST.get('addr_contacts')
				recipients = handle_addr_book(viewer, meeting, added, False)

				if recipients:
					send_email_invite(meeting, viewer.user, recipients)

			if 'settings' in request.POST:
				return HttpResponseRedirect('../settings/')

			if 'members' in request.POST:
				return HttpResponseRedirect('../managemembers/')

			if 'join_meeting' in request.POST and viewer:
				context['joined'] = True
				viewer.meetings_in.add(meeting)
				meeting.members.add(viewer)
				viewer.save()
				meeting.save()

				if viewer.user.email in meeting.invited:
					title = meeting.title+': '+viewer.user.first_name+' '+viewer.user.last_name+' has joined.'
					message = SIGNATURE
					send_mail(title, message, SENDER, [host.user.email])

			
	if meeting.m_type == 'Interview': 
		question = None
		question_period = (meeting.q_started and not meeting.q_ended)
		context['can_ask'] = False

		if question_period:
			context['question_period'] = True
			if request.user.is_authenticated():
				context['can_ask'] = True
				if (viewer.user.email == meeting.invitee) or (viewer == host):
					context['can_ask'] = False
				if not meeting.accepted:
					context['can_ask'] = False
					context['question_period'] = False


				context['asked'] = False
				for q in meeting.questions.all():
					if viewer==q.user:
						context['asked'] = True
						context['question'] = q
						question = q

		if request.user.is_authenticated():
			context['is_invitee'] = False
			if (viewer.user.email == meeting.invitee):
				context['is_invitee'] = True

		if meeting.started and not meeting.ended:
			context['active_period'] = True
		else:
			context['active_period'] = False

		invalid_qtime = (not meeting.q_started or meeting.q_ended)

		if request.method=='POST' and not closed:
			# if context['access'] == False:
			if viewer.user.email == meeting.invitee:
				if ('accept' in request.POST or 'decline' in request.POST) and not meeting.agreed_yet:
					title = 'Invitee Response: '+meeting.title
					message = viewer.user.first_name+' '+viewer.user.last_name+' has '
					if 'accept' in request.POST:
						meeting.accepted = True
						meeting.agreed_yet = True
						response_message = 'Thanks! You have accepted this meeting invitation.'
						message += 'accepted '

						recipients = []

						# send held emails
						if meeting.pending:
							emails = meeting.pending.split(',')
							for e in emails:
								if '@' in e:
									recipients.append(e)
							if recipients:
								send_email_invite(meeting, viewer.user, recipients)
							meeting.pending = ''

					elif 'decline' in request.POST:
						meeting.accepted = False
						meeting.agreed_yet = True
						response_message = 'Thanks! You have declined this meeting invitation.'
						message += 'declined '

					context['joined'] = True
					viewer.meetings_in.add(meeting)
					meeting.members.add(viewer)
					viewer.save()
					meeting.save()

					# notify host of response
					response_message += ' The host will be notified of your decision.'
					message += 'your invitation to be interviewed.'+SIGNATURE
					context['response_message'] = response_message
					context['show_response_options'] = False

					if EMAILS_ENABLED:
						send_mail(title, message, SENDER, [host.user.email])

			if question_period:
				if 'q_asked' in request.POST:
					q = Question(title=request.POST['title'], user=viewer,
						body=request.POST['body'], timestamp=dtnow, selected=False)
					q.save()
					meeting.questions.add(q)
					meeting.save()
					context['asked'] = True
					context['question'] = q
				elif 'q_edited' in request.POST:
					if question:
						question.title = request.POST['title']
						question.body = request.POST['body']
						question.save()
			if 'change_answer' in request.POST:
				q = Question.objects.get(id__exact=request.POST.get('q_id'))
				q.answer = request.POST.get('answertext')
				q.save()
			if 'response' in request.POST:
				q = Question.objects.get(id__exact=request.POST.get('q_id'))
				q.answer = request.POST.get('response')
				q.save()

			if 'qgroup' in request.POST:
				q = Question.objects.get(id__exact=request.POST.get('qgroup'))
				q.selected = True
				q.save()


		if viewer:
			if meeting.accepted is not True and meeting.accepted is not False:
				context['not_responded'] = True
				if viewer.user.email == meeting.invitee:
					context['show_response_options'] = True

		q_unsent = []
		q_sent = []

		for q in meeting.questions.all():
			if q.selected:
				q_sent.append(q)
			else:
				q_unsent.append(q)

		context['m'] = meeting
		context['q_unsent'] = q_unsent
		context['q_sent'] = q_sent
		context['user'] = request.user
		context['host'] = host

		request.session['meeting_no'] = path
		request.session.modified=True

		return render_to_response('interview_page.html', context)

	elif meeting.m_type == 'Chat':
		context['closed'] = closed

		if viewer and viewer not in meeting.chat.online.all():
			meeting.chat.online.add(viewer)
			meeting.chat.save()

		online = meeting.chat.online.all()

		context['online'] = online
		context['num_online'] = len(online)

		if meeting.chat.chatlog != '':
			context['chatlog'] = meeting.chat.chatlog
		if request.method=='POST' and not closed:
			if 'close_bans' in request.POST:
				if viewer in meeting.moderators.all() or viewer==host:
					dtnow = (ZONE.localize(datetime.now())).astimezone(meetingtz)
					time = dtnow.strftime("%H:%M:%S")
					bans = request.POST.get('ban_list')
					unbans = request.POST.get('unban_list')
					if bans:
						bans = bans.split(' ')
						for m_id in bans:
							if m_id == '':
								continue
							member = meeting.members.filter(id__exact=m_id)
							if member:
								member = member[0]
								if member != host and member.user.email != meeting.invitee:
									if member not in meeting.chat.banlist.all():
										meeting.chat.banlist.add(member)
										meeting.chat.chatlog += "<div class='msgln'><text style='color:red; font-style: italic;'>("+time+") "+ viewer.user.first_name+" "+viewer.user.last_name+" has banned "+member.user.first_name+" "+member.user.last_name+" from this chat.</text><br></div>"
										meeting.chat.save()
					if unbans:
						unbans = unbans.split(' ')
						for m_id in unbans:
							if m_id == '':
								continue
							member = meeting.members.filter(id__exact=m_id)
							if member:
								member = member[0]
								if member in meeting.chat.banlist.all():
									meeting.chat.banlist.remove(member)
									meeting.chat.chatlog += "<div class='msgln'><text style='color:blue; font-style: italic;'>("+time+") "+ viewer.user.first_name+" "+viewer.user.last_name+" has unbanned "+member.user.first_name+" "+member.user.last_name+" from this chat.</text><br></div>"
									meeting.chat.save()


		context['m'] = meeting
		context['user'] = request.user
		context['host'] = host

		request.session['meeting_no'] = path
		request.session.modified = True

		return render_to_response('interactive_page.html', context)
	else:
		if request.method=='POST':
			if request.POST.get('motionname'):
				motiontext = request.POST.get('motiontext')
				motionname = request.POST.get('motionname')
				if motionname:
					motion = Motion(user=Account.objects.get(user=request.user), timestamp=dtnow, 
						name=motionname, desc=motiontext, likes=0, dislikes=0, pastname=motionname,
						pastdesc=motiontext, modded=False)
					motion.save()

					ai_id = request.POST.get('agendaid')
					modified_ai = AgendaItem.objects.get(id__exact=ai_id)
					modified_ai.motions.add(motion)
					modified_ai.save()

					recipients = []
					for mem in meeting.members.all():
						if meeting in mem.receive_emails.all():
							e = mem.user.email
							recipients.append(e)

					message = 'A new motion has been added by '+request.user.first_name+' '+request.user.last_name+' to the following agenda item: "'+modified_ai.name+'". \n\nThe motion title is: '+motion.name+'.\n\n You can visit the meeting page and view this motion at http://vitalmeeting.com/meeting/'+meeting.meeting_id+'.'+SIGNATURE
					title = meeting.title + ': New Motion Added'
					if EMAILS_ENABLED:
						send_mail(title, message, SENDER, recipients)

			if request.POST.get('comment'):
				comment = request.POST.get('comment')
				if comment:
					comment = Comment(user=Account.objects.get(user=request.user), timestamp=dtnow,
						text=comment, pasttext=comment, modded=False)
					comment.save()

					motion_id = request.POST.get('motionid')
					modified_motion = Motion.objects.get(id__exact=motion_id)
					modified_motion.comments.add(comment)
					modified_motion.save()

					recipients = []
					if meeting in meeting.hosts.all()[0].receive_emails.all():
						recipients.append(meeting.hosts.all()[0].user.email)
					if meeting in modified_motion.user.receive_emails.all():
						recipients.append(modified_motion.user.user.email)

					message = 'A new comment has been added by '+request.user.first_name+' '+request.user.last_name+' to the following motion: "'+modified_motion.name+'". \n\nThe comment reads: "'+comment.text+'".\n\nYou can visit the meeting page and view this comment at http://vitalmeeting.com/meeting/'+meeting.meeting_id+'.'+SIGNATURE
					title = meeting.title + ': New Comment Added'
					if modified_motion.user in meeting.members.all():
						if EMAILS_ENABLED:
							send_mail(title, message, SENDER, recipients)

			account = Account.objects.filter(user=request.user)
			if 'remove_motion' in request.POST:
				motion_id = request.POST.get('remove_motion')
				motion = Motion.objects.get(id__exact=motion_id)
				if account and account[0] == motion.user:
					motion.name = 'This motion has been removed by its author.'
				elif account and (account[0] in meeting.moderators.all() or account[0] == meeting.hosts.all()[0]):
					former_name = motion.name
					motion.name = 'This motion has been removed by a moderator.'
					recipient = [motion.user.user.email]
					message = 'Your motion "'+former_name+'" in meeting "'+meeting.title+'" has been removed by a moderator.\n\n\n\nVitalMeeting.com\nStructured Online Meetings'
					if motion.user in meeting.members.all():
						if EMAILS_ENABLED:
							send_mail("Motion removed", message, SENDER, recipient)
				motion.desc = ''
				motion.modded = True
				motion.save()

			if 'remove_comment' in request.POST:
				ids = request.POST.get('remove_comment').split(" ")
				comment_id = ids[0]
				motion_id = ids[1]
				comment = Comment.objects.get(id__exact=comment_id)
				if account and account[0] == comment.user:
					comment.text = 'This comment has been removed by its author.'
				elif account and (account[0] in meeting.moderators.all() or account[0] == meeting.hosts.all()[0]):
					comment.text = 'This comment has been removed by a moderator.'
					recipient = [comment.user.user.email]
					motion = Motion.objects.get(id__exact=motion_id)
					message = 'Your comment on motion "'+motion.name+'" in meeting "'+meeting.title+'" has been removed by a moderator.\n\n\n\nVitalMeeting.com\nStructured Online Meetings'
					if EMAILS_ENABLED:
						send_mail("Comment removed", message, SENDER, recipient)

				comment.modded = True
				comment.save()

			if 'change_motion' in request.POST:
				m_id = request.POST.get('m_id')
				text = request.POST.get('motiontext')
				title = request.POST.get('m_title')
				motion = Motion.objects.get(id__exact=m_id)
				motion.name = title
				motion.desc = text
				motion.save()

			if 'change_ai' in request.POST:
				ai_id = request.POST.get('ai_id')
				name = request.POST.get('name')
				ai = AgendaItem.objects.get(id__exact=ai_id)
				ai.name = name
				ai.save()

			if 'change_comment' in request.POST:
				c_id = request.POST.get('c_id')
				text = request.POST.get('commenttext')
				comment = Comment.objects.get(id__exact=c_id)
				comment.text = text
				comment.save()

		request.session['meeting_no'] = path
		request.session.modified=True

		context['m'] = meeting
		context['host'] = host

		org = meeting.organizations.all()
		if org:
			context['org'] = org[0]

		agenda_items = meeting.agenda_items.all().order_by('id')
		context['agenda_items'] = agenda_items
		return render_to_response('meeting_page.html', context)

def settings(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user
	form = SettingsForm()
	context['form'] = form

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	meeting = Meeting.objects.filter(meeting_id__exact=request.session['meeting_no'])
	if not meeting:
		return HttpResponseRedirect('..')
	meeting = meeting[0]
	if request.user != meeting.hosts.all()[0].user:
		return HttpResponseRedirect('..')

	context['meeting'] = meeting
	context['agenda_items'] = meeting.agenda_items.all().reverse()

	if request.method == 'POST':
		form = SettingsForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			if cd['title']:
				meeting.title = cd['title']
			if cd['desc']:
				meeting.desc = cd['desc']
			if cd['startdate']:
				meeting.startdate = cd['startdate']
			if cd['starttime']:
				meeting.starttime = cd['starttime']
			if cd['enddate']:
				meeting.enddate = cd['enddate']
			if cd['endtime']:
				meeting.endtime = cd['endtime']
			if cd['status']:
				if cd['status'] == 'Private':
					meeting.private = True
				else:
					meeting.private = False
			if cd['fi']:
				if cd['fi'] == 'Yes':
					meeting.friend_invites = True
				else:
					meeting.friend_invites = False
			removed = request.POST.get('removed')
			if removed:
				removed = removed.split(',')
				for ai in removed:
					if ai != '':
						ai = AgendaItem.objects.get(id__exact=ai)
						meeting.agenda_items.remove(ai)

			counter = 1
			item_name = 'agenda_item_'+str(counter)
			while request.POST.get(item_name):
				agendaitem = request.POST.get(item_name)
				if agendaitem:
					i = AgendaItem(name=agendaitem, desc='', number=counter)
					i.save()
					meeting.agenda_items.add(i)
					meeting.save()
				counter += 1
				item_name = 'agenda_item_'+str(counter)

			meeting.save()
			
		else:
			errors = {}
			context['errors'] = errors

	context['form'] = form

	return render_to_response('settings.html', context)

def managemembers(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	useraccount = Account.objects.get(user=request.user)

	meeting = Meeting.objects.filter(meeting_id__exact=request.session['meeting_no'])
	if not meeting:
		return HttpResponseRedirect('..')
	meeting = meeting[0]
	if request.user != meeting.hosts.all()[0].user:
		return HttpResponseRedirect('..')

	context['meeting'] = meeting
	recipients = []

	if request.POST:
		add_from_c = request.POST.get('from_contacts')
		remove = request.POST.get('remove_contacts')
		promote = request.POST.get('promote_members')

		if add_from_c:
			added = add_from_c.split(' ')
			for c_id in added:
				if c_id != '':
					contact = a.contacts.filter(id__exact=c_id)
					if contact:
						contact = contact[0]
						meeting.invited += contact.email + ','
						meeting.save()

						recipients.append(contact.email)

		if remove:
			remove = remove.split(' ')
			for m_id in added:
				if m_id != '':
					mem = meeting.members.filter(id__exact=m_id)
					if mem:
						mem = mem[0]
						meeting.members.remove(mem)
						meeting.save()
						mem.meetings_in.remove()
						mem.save()

		if promote:
			promote = promote.split(' ')
			for m_id in promote:
				if m_id != '':
					mod = meeting.members.filter(id__exact=m_id)
					if mod:
						mod = mod[0]
						meeting.moderators.add(mod)
						meeting.save()

		if request.POST.get('entered'):
			entered = request.POST.get('entered')
			entered = entered.split('\n')

			for e in entered:
				e = e.strip('\r')
				meeting.invited += e + ','
				meeting.save()

				recipients.append(e.strip('\r'))

		if request.POST.get('addr_contacts'):
			added = request.POST.get('addr_contacts')
			addr_book_c += handle_addr_book(useraccount, meeting, added, False)

			recipients += addr_book_c

			for c in addr_book_c:
				meeting.invited += c + ','
			meeting.save()

		if recipients:
			send_email_invite(meeting, request.user, recipients)

	members_to_mod = []
	members_to_remove = []
	for m in meeting.members.all():
		if m not in meeting.moderators.all() and m not in meeting.hosts.all():
			members_to_mod.append(m)
		if m not in meeting.hosts.all():
			members_to_remove.append(m)
	context['members_to_mod'] = members_to_mod
	context['members_to_remove'] = members_to_remove

	contacts = []
	for c in useraccount.contacts.all():
		if c.account:
			if c.account not in meeting.members.all() and c.account not in meeting.hosts.all():
				contacts.append(c)
		elif c.email not in meeting.invited:
			contacts.append(c)
	context['contacts'] = contacts

	return render_to_response('managemembers.html', context)

def attachorg(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	form = MeetingOrgForm()

	if not request.user.is_authenticated() and not 'account' in request.session:
		return HttpResponseRedirect('/')

	if not 'account' in request.session:
		a = Account.objects.get(user=request.user)
	else:
		a = request.session['account']

	context['orgs'] = a.organizations.all()

	m = Meeting.objects.filter(meeting_id__exact=request.session['meeting_created'])
	if m:
		m = m[0]
	else:
		return HttpResponseRedirect('/')

	if request.method=='POST':
		if 'later' in request.POST:
			return HttpResponseRedirect('../invite/')
		form = MeetingOrgForm(request.POST, request.FILES)
		if form.is_valid():
			cd = form.cleaned_data
			userinput = ((cd['name'] != '' or cd['contact'] != '') or cd['desc'] != '') or cd['image'] is not None
			formerror = ((cd['name'] == '' or cd['contact'] == '') or cd['desc'] == '')
			if userinput and formerror:
				context['input_error'] = True
				if cd['name'] == '':
					context['name_error'] = True
				if cd['desc'] == '':
					context['desc_error'] = True
				if cd['contact'] == '':
					context['contact_error'] = True
			elif userinput:
				random.seed()

				pid = ''
				for i in range(22):
					# TODO: add upper/lower case letters as well for extra protection
					pid += chr(int(random.random()*25)+97)

				o = Organization(name=cd['name'], desc=cd['desc'], image=cd['image'], contact=cd['contact'], website=cd['website'], page_id=pid)
				o.save()
				o.manager.add(a)
				o.save()
				a.organizations.add(o)
				a.save()

				m.organizations.add(o)
				m.save()

				if cd['image'] is not None:
					path = os.path.join(dsettings.MEDIA_ROOT, o.image.url)
					tn= Image.open(path)
					tn.thumbnail((200, 200), Image.ANTIALIAS)
					tn.save(path)

				return HttpResponseRedirect('../invite/')
			else:
				selected = request.POST['selectorg']
				if selected is not None and selected != 'None\n':
					o = Organization.objects.filter(id__exact=selected)
					if o:
						o = o[0]
						m.organizations.add(o)
						m.save()

						return HttpResponseRedirect('../invite/')
					else:
						context['get_org_error'] = True

		else:
			errors = {}
			context['errors'] = errors

	context['form'] = form
	return render_to_response('attachorg.html', context)

def orgpage(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user
	emailform = OrgEmailForm()
	form = ImgForm()

	if request.user.is_authenticated():
		viewer = Account.objects.get(user=request.user)
		context['viewer'] = viewer

	path = ''
	if 'orgs' in request.path:
		path = request.path.split('/')[2]

	org = Organization.objects.filter(page_id__exact=path)
	if org:
		org = org[0]
		context['org'] = org
	else:
		return HttpResponseRedirect('/')

	context['manager'] = org.manager.all()[0]

	if request.POST:
		# check for the button; that way, cancel can be a submit too
		if 'pic' in request.POST:
			form = ImgForm(request.POST, request.FILES)
			if form.is_valid():
				cd = form.cleaned_data
				org.image = cd['image']
				org.save()
				if cd['image'] is not None:
					path = os.path.join(dsettings.MEDIA_ROOT, org.image.url)
					tn= Image.open(path)
					tn.thumbnail((200, 200), Image.ANTIALIAS)
					tn.save(path)

		if 'change_contact' in request.POST:
			emailform = OrgEmailForm(request.POST)
			if emailform.is_valid():
				cd = emailform.cleaned_data;
				org.contact = cd['contact']
			else:
				errors = {}
				context['errors'] = errors
		if 'change_desc' in request.POST:
			desc = request.POST.get('desc')
			if desc is not None:
				org.desc = desc
		if 'change_ws' in request.POST:
			ws = request.POST.get('ws')
			org.website = ws
		org.save()

	context['emailform'] = emailform
	context['form'] = form

	return render_to_response('orgpage.html', context)

def profpage(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if request.user.is_authenticated():
		viewer = Account.objects.get(user=request.user)
		context['viewer'] = viewer

	path = ''
	if 'profile' in request.path:
		path = request.path.split('/')[2]

	account = Account.objects.filter(page_id__exact=path)
	if account:
		account = account[0]
		context['account'] = account
	else:
		return render_to_response('error.html') # TODO

	return render_to_response('profpage.html', context)


