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
from django.utils import simplejson
import re, os
from django.core.mail import send_mail
from django.conf import settings as dsettings
from PIL import Image, ImageOps
from pytz import timezone
import pytz
#import requests

SENDER = 'Vital Meeting <info@vitalmeeting.com>'
SIGNATURE = '\n\n\n\nVitalMeeting.com\nStructured Online Meetings'
UTC = pytz.utc
ZONE = timezone('America/Chicago')


def mailgun_send(recipients, subject, message):
	return requests.post(
		"https://api.mailgun.net/v2/rs3945.mailgun.org/messages",
		auth=("api", "key-6jh7x-u493r23q8bi-cgkntmlcbc7pd1"),
		data={"from": "VitalMeeting <updates@rs3945.mailgun.org>",
				"to": recipients,
				"subject": subject,
				"text": message})

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

				s = True
				if cd['status'] == 'Public':
					s=False

				random.seed()

				meeting_no = ''
				for i in range(15):
					# TODO: add upper/lower case letters as well for extra protection
					meeting_no += chr(int(random.random()*25)+97)

				# these should hopefully return timedeltas and work
				already_started = False
				already_ended = False

				enteredtimestart = datetime.combine(cd['startdate'], cd['starttime'])
				enteredtimeend = datetime.combine(cd['enddate'], cd['endtime'])
				
				tz = cd['timezone']
				meetingtz = timezone(tz)
				enteredtimestart = meetingtz.localize(enteredtimestart)
				enteredtimeend = meetingtz.localize(enteredtimeend)

				rightnow = (ZONE.localize(datetime.now())).astimezone(meetingtz)

				if (rightnow-enteredtimestart).total_seconds() > 0:
					already_started = True
				if (rightnow-enteredtimeend).total_seconds() > 0:
					already_ended = True


				m = Meeting(startdate=cd['startdate'], starttime=cd['starttime'], enddate=cd['enddate'],
					endtime=cd['endtime'], title=cd['title'], desc=cd['desc'], private=s, meeting_id=meeting_no, 
					started=already_started, ended=already_ended, timezone=cd['timezone'])
				m.save()
				m.hosts.add(a)
				m.members.add(a)
				m.save()

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

				a.meetings_created.add(m)
				a.meetings_in.add(m)
				a.save()

				request.session['meeting_created'] = meeting_no
				request.session.modified=True

				return HttpResponseRedirect('../attachorg/')
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

	if request.method=='POST':
		if "later" in request.POST:
			return HttpResponseRedirect('../meeting/'+meeting_no)

		added = request.POST.get('added')
		entered = request.POST.get('entered')

		recipients = []

		if added:
			added = added.split(',')
			for entry in added:
				if '@' not in entry:
					continue
				e = entry.split('<')
				e = e[1].split('>')[0]

				meeting.invited += e + ',' #csv
				meeting.save()

				c = Contact.objects.filter(email=e)
				if c:
					c = c[0]
					if c.account:
						account = c.account
						meeting.members.add(account)
						account.meetings_in.add(meeting)
						account.save()
						meeting.save()
					recipients.append(e)


		if request.POST.get('entered'):
			entered = request.POST.get('entered').split('\n')

			for e in entered:
				e = e.strip('\r')
				meeting.invited += e + ','
				acct = Account.objects.filter(user=User.objects.get(email=e))
				if acct:
					acct = acct[0]
					acct.meetings_in.add(meeting)
					meeting.members.add(acct)
					acct.save()
				meeting.save()
				recipients.append(e)

		if recipients:
			title = "Meeting Invite: " + meeting.title
			message = ("You've been invited to attend " + a.user.first_name + " " + a.user.last_name + "'s online meeting discussion, " +
						"on VitalMeeting.com.\n\nPlease click on " +
						"http://www.vitalmeeting.com/meeting/"+meeting.meeting_id+" to join in.\n\n\n\nVitalMeeting.com\nStructured Online Meetings")

			send_mail(title, message, SENDER, recipients)

		request.session['account'] = ''
		request.session.modified = True
		return HttpResponseRedirect('../meeting/'+meeting_no)

	return render_to_response('invite.html', context)

def signup(request):
	context = {}
	context.update(csrf(request))
	form = UserForm(request.POST, request.FILES)
	context['form'] = form

	if request.user.is_authenticated():
		return HttpResponseRedirect('../home/')

	if request.method == 'POST':
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
					message = 'Please go to http://www.vitalmeeting.com/verify/'+vkey+' to verify your account. Thanks!\n\n\n\nVitalMeeting.com\nStructured Online Meetings'
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
				cd = form.cleaned_data

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

	if request.method == 'POST':
		form = ContactForm(request.POST)
		if 'new_contact' in request.POST:
			if form.is_valid():
				cd = form.cleaned_data;
				u = User.objects.filter(email__exact=cd['email'])
				matching_account = None
				if u:
					matching_account = Account.objects.get(user=u)
				c = Contact(title=cd['title'], first_name=cd['first_name'], last_name=cd['last_name'],
						email=cd['email'], address=cd['address'], wphone=cd['wphone'], hphone=cd['hphone'])
				if matching_account:
					c.account = matching_account
				c.save()
				a.contacts.add(c)
				a.save()
			else:
				context['errors'] = 'error'

		if request.POST.get('remove_contact'):
			cid = request.POST.get('remove_contact')
			contact = Contact.objects.get(id__exact=cid)
			a.contacts.remove(contact)
			a.save()
	
	context['contacts'] = contacts
	context['form'] = form

	return render_to_response('contacts.html', context)

def addorganizer(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	context = {}
	context.update(csrf(request))
	form = OrganizationForm()
	context['form'] = form
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

			o = Organization(name=cd['name'], desc=cd['desc'], image=cd['image'], contact=cd['contact'], page_id=pid)
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
			context['errors'] = 'errors'

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

	context['access'] = True
	try:
		meetingtz = timezone(meeting.timezone)
	except:
		meetingtz = UTC

	if meeting.private:
		if not request.user.is_authenticated():
			#return HttpResponseRedirect('/')
			context['access'] = False
			context['not_authenticated'] = True
		elif meeting.hosts.all()[0] != Account.objects.get(user=request.user):
				if request.user.email not in meeting.invited:
					context['access'] = False
					context['not_invited'] = True
					return HttpResponseRedirect('/')

		#if Account.objects.get(user=request.user) not in meeting.members.all():
			#return HttpResponseRedirect('/')

	if request.user.is_authenticated():
		viewer = Account.objects.get(user=request.user)
		if request.user.email in meeting.invited:
			if meeting not in viewer.meetings_in.all():
				viewer.meetings_in.add(meeting)
				viewer.save()

	if request.method=='POST':
		# if context['access'] == False:
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
		elif (not meeting.started or meeting.ended) and (request.user != meeting.hosts.all()[0].user):
			context['closed_error'] = True
		else:
			if request.POST.get('motionname'):
				motiontext = request.POST.get('motiontext')
				motionname = request.POST.get('motionname')
				if motionname:
					motion = Motion(user=Account.objects.get(user=request.user), timestamp=(ZONE.localize(datetime.now())).astimezone(meetingtz), 
						name=motionname, desc=motiontext, likes=0, dislikes=0, pastname=motionname,
						pastdesc=motiontext, modded=False)
					motion.save()

					ai_id = request.POST.get('agendaid')
					modified_ai = AgendaItem.objects.get(id__exact=ai_id)
					modified_ai.motions.add(motion)
					modified_ai.save()

					recipients = []
					recipients.append(meeting.hosts.all()[0].user.email)
					for e in meeting.invited.split(','):
						if '@' in e:
							recipients.append(e)

					message = 'A new motion has been added by '+request.user.first_name+' '+request.user.last_name+' to the following agenda item: "'+modified_ai.name+'". You can visit the meeting page and view this motion at http://www.vitalmeeting.com/meeting/'+meeting.meeting_id+'.'+SIGNATURE
					title = meeting.title + ': New Motion Added'
					send_mail(title, message, SENDER, recipients)

			if request.POST.get('comment'):
				comment = request.POST.get('comment')
				if comment:
					comment = Comment(user=Account.objects.get(user=request.user), timestamp=(ZONE.localize(datetime.now())).astimezone(meetingtz),
						text=comment, pasttext=comment, modded=False)
					comment.save()

					motion_id = request.POST.get('motionid')
					modified_motion = Motion.objects.get(id__exact=motion_id)
					modified_motion.comments.add(comment)
					modified_motion.save()

					recipients = []
					recipients.append(meeting.hosts.all()[0].user.email)
					recipients.append(modified_motion.user.user.email)

					message = 'A new comment has been added by '+request.user.first_name+' '+request.user.last_name+' to the following motion: "'+modified_motion.name+'". You can visit the meeting page and view this comment at http://www.vitalmeeting.com/meeting/'+meeting.meeting_id+'.'+SIGNATURE
					title = meeting.title + ': New Comment Added'
					send_mail(title, message, SENDER, recipients)

			if 'settings' in request.POST:
				return HttpResponseRedirect('../settings/')

			if 'members' in request.POST:
				return HttpResponseRedirect('../managemembers/')

			account = Account.objects.filter(user=request.user)
			if 'remove_motion' in request.POST:
				motion_id = request.POST.get('remove_motion')
				motion = Motion.objects.get(id__exact=motion_id)
				if account and account[0] == motion.user:
					motion.name = 'This motion has been removed by its author.'
				if account and (account[0] in meeting.moderators.all() or account[0] == meeting.hosts.all()[0]):
					motion.name = 'This motion has been removed by a moderator.'
					recipient = [motion.user.user.email]
					message = 'Your motion "'+motion.name+'" in meeting "'+meeting.title+'" has been removed by a moderator.\n\n\n\nVitalMeeting.com\nStructured Online Meetings'
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
	context['host'] = meeting.hosts.all()[0]
	agenda_items = meeting.agenda_items.order_by('number')
	context['agenda_items'] = agenda_items

	org = meeting.organizations.all()
	if org:
		context['org'] = org[0]

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

			removed = request.POST.get('removed')
			if removed:
				removed = removed.split(',')
				print removed
				for ai in removed:
					if ai != '':
						ai = AgendaItem.objects.get(id__exact=ai)
						meeting.agenda_items.remove(ai)

			counter = 1
			item_name = 'agenda_item_'+str(counter)
			while request.POST.get(item_name):
				agendaitem = request.POST.get(item_name)
				if agendaitem:
					i = AgendaItem(name=agendaitem, desc='')
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
		added1 = request.POST.get('added1')
		added2 = request.POST.get('added2')
		added3 = request.POST.get('added3')

		if added1:
			added1 = added1.split(',')
			for entry in added1:
				if '@' not in entry:
					continue
				e = entry.split('<')
				e = e[1].split('>')[0]

				meeting.invited += e + ','
				meeting.save()

				c = Contact.objects.filter(email=e)
				if c:
					c = c[0]
					if c.account:
						account = c.account
						meeting.members.add(account)
						account.meetings_in.add(meeting)
						account.save()
						meeting.save()
				recipients.append(e)
		if added2:
			added2 = added2.split(',')

			for entry in added2:
				if '@' not in entry:
					continue
				e = entry.split('<')
				e = e[1].split('>')[0]
				u = User.objects.filter(email=e)
				if u:
					account = Account.objects.get(user=u[0])
					meeting.members.remove(account)
					account.meetings_in.remove(meeting)
					account.save()
					meeting.save()

		if added3:
			added3 = added3.split(',')

			for entry in added3:
				if '@' not in entry:
					continue
				e = entry.split('<')
				e = e[1].split('>')[0]

				# TEST THIS
				meeting.invited = re.sub(e+',', '', meeting.invited)
				meeting.save()

				u = User.objects.filter(email=e)
				if u:
					account = Account.objects.get(user=u[0])
					meeting.moderators.add(account)
					meeting.save()

		if request.POST.get('entered'):
			entered = request.POST.get('entered')
			entered = entered.split('\n')

			for e in entered:
				e = e.strip('\r')
				meeting.invited += e + ','
				acct = Account.objects.filter(user=User.objects.get(email=e))
				if acct:
					acct = acct[0]
					acct.meetings_in.add(meeting)
					meeting.members.add(acct)
					acct.save()
				meeting.save()

				recipients.append(e.strip('\r'))

		if recipients:
			title = "Meeting Invite: " + meeting.title
			message = ("You've been invited to attend " + request.user.first_name + " " + request.user.last_name + "'s online meeting discussion, " +
						"on VitalMeeting.com.\n\nPlease click on " +
						"http://www.vitalmeeting.com/meeting/"+meeting.meeting_id+" to join in.\n\n\n\nVitalMeeting.com\nStructured Online Meetings")

			send_mail(title, message, SENDER, recipients)

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
			if c.email not in meeting.invited and c not in meeting.hosts.all():
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
	context['form'] = form

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

	if request.POST:
		if 'later' in request.POST:
			return HttpResponseRedirect('../invite/')
		form = MeetingOrgForm(request.POST, request.FILES)
		if form.is_valid():
			cd = form.cleaned_data
			userinput = ((cd['name'] != '' or cd['contact'] != '') or cd['desc'] != '') or cd['image'] is not None
			formerror = ((cd['name'] == '' or cd['contact'] == '') or cd['desc'] == '')
			if userinput and formerror:
				if cd['name'] == '':
					context['form.name.errors'] = True
				if cd['desc'] == '':
					context['form.desc.errors'] = True
				if cd['contact'] == '':
					context['form.contact.errors'] = True
			elif userinput:
				random.seed()

				pid = ''
				for i in range(22):
					# TODO: add upper/lower case letters as well for extra protection
					pid += chr(int(random.random()*25)+97)

				o = Organization(name=cd['name'], desc=cd['desc'], image=cd['image'], contact=cd['contact'], page_id=pid)
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
			context['errors'] = 'errors'


	return render_to_response('attachorg.html', context)

def orgpage(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

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


