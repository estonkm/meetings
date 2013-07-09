# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render_to_response
from django.template import RequestContext
from django.core.context_processors import csrf
from data.forms import MeetingForm, UserForm, SettingsForm
from data.models import Account, Meeting, AgendaItem, Motion, Comment
from django.contrib.auth.models import User
from datetime import datetime, date
import time
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
import random
from django.core.urlresolvers import resolve
from django.utils import simplejson
import re
from django.core.mail import send_mail
import requests

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

	if not request.user.is_authenticated():
		request.session['fromcreate'] = True
		request.session.modified = True
		return HttpResponseRedirect('../signup/')

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
				if cd['status'] == 'Public':
					s=False

				random.seed()

				meeting_no = ''
				for i in range(15):
					# TODO: add upper/lower case letters as well for extra protection
					meeting_no += chr(int(random.random()*25)+97)

				# these should hopefully return timedeltas and work
				already_started = False

				enteredtime = datetime.combine(cd['startdate'], cd['starttime'])
				rightnow = datetime.now()
				if (rightnow-enteredtime).total_seconds() > 0:
					already_started = True

				m = Meeting(startdate=cd['startdate'], starttime=cd['starttime'], enddate=cd['enddate'],
					endtime=cd['endtime'], title=cd['title'], desc=cd['desc'], private=s, meeting_id=meeting_no, 
					started=already_started, ended=False, timezone=cd['timezone'])
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

				request.session['meeting_no'] = meeting_no
				request.session.modified=True

				return HttpResponseRedirect('../invite/')
			else:
				errors = {}
				context['errors'] = errors

	context['form'] = form

	return render_to_response('create.html', context)

def invite(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if not request.user.is_authenticated():
		return HttpResponseRedirect('../signup/')

	context['account'] = Account.objects.get(user=request.user)

	meeting_no = request.session['meeting_no']

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
				u = User.objects.filter(email=e)
				if u:
					account = Account.objects.get(user=u[0])
					recipients.append(e)
					meeting.members.add(account)
					account.meetings_in.add(meeting)
					account.save()
					meeting.save()

		if request.POST.get('entered'):
			entered = entered.split('\n')

			for e in entered:
				recipients.append(e)

		if recipients:
			message = (request.user.first_name + " " + request.user.last_name + " has invited you to the meeting " +
					meeting.title + ", which begins at " + str(meeting.starttime) + ", " + str(meeting.startdate) + ". You can find the meeting at: " +
					"http://www.vitalmeeting.herokuapps.com/meeting/"+meeting_no)

		#	send_mail(meeting.title, message, "vitalmeeting@gmail.com", recipients)

		return HttpResponseRedirect('../meeting/'+meeting_no)

	return render_to_response('invite.html', context)

#TODO: hash email to form username (otherwise too easy to get permissions on meeting page)

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

					random.seed()

					for i in range(25):
						vkey += chr(int(random.random()*25)+97)

					u = User.objects.create_user(cd['email'], first_name=cd['first_name'],
						last_name=cd['last_name'], email=cd['email'], password=cd['password'])
					a = Account(user=u, join_date=datetime.now(), phone='', is_verified=False, verification_key=vkey) 
					a.save()
					# TODO - use verification and don't log on just yet
					recipient = ['splichte@princeton.edu']
					message = 'Please go to http://www.vitalmeeting.com/verify/'+vkey+' to verify your account. Thanks!'
					send_mail('Account Verification', message, 'Vital Meeting <info@vitalmeeting.com>', recipient)

					#user = authenticate(username=cd['email'], password=cd['password'])
					#auth_login(request, user)

					if 'fromcreate' in request.session:
						return HttpResponseRedirect('../create/')
					else:
						return HttpResponseRedirect('../home/')
			else:
				errors = {}
				context['errors'] = errors
				cd = form.cleaned_data

	return render_to_response('signup.html', context)

def verify(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	if not user.is_authenticated():
		path = ''
		if 'verify' in request.path:
			path = request.path.split('/')[2]
		else:
			return HttpResponseRedirect('..')

		a = Account.objects.filter(id__exact=path)
		if not a:
			return HttpResponseRedirect('..')
		else:
			u = a[0].user
			a[0].is_verified = True
			a[0].save()
			user = authenticate(username=u.username, password=u.password)
			auth_login(request, user)

			if 'meeting_no' in request.session:
				context['meeting'] = request.session['meeting_no']
			return render_to_response('verify.html', context)
	else:
		return HttpResponseRedirect('../home/')

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

	return render_to_response('home.html', context)

def profile(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	account = Account.objects.get(user=request.user)
	context['account'] = account

	return render_to_response('profile.html', context)

def contacts(request):
	context = {}
	context.update(csrf(request))
	context['user'] = request.user

	a = Account.objects.get(user=request.user)
	contacts = a.contacts.all()

	context['meetings'] = a.meetings_in.all()

	if request.method == 'POST':
		query = request.POST.get('search')
		if query:
			u = User.objects.filter(email=query)
			if u:
				b = Account.objects.get(user=u[0])
				a.contacts.add(b)
				a.save()
				context['result'] = b.user.username + ' was successfully added to your contacts.'
			else:
				context['errors'] = 'error'
		if request.POST.get('remove_contact'):
			cid = request.POST.get('remove_contact')
			contact = Account.objects.get(id__exact=cid)
			a.contacts.remove(contact)
			a.save()
	
	context['contacts'] = contacts

	return render_to_response('contacts.html', context)

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
		return render_to_response('error.html') # TODO

	if meeting.private:
		if not request.user.is_authenticated():
			return HttpResponseRedirect('/')
		if Account.objects.get(user=request.user) not in meeting.members.all():
			return HttpResponseRedirect('/')

	if request.method=='POST':
		if request.POST.get('motionname'):
			motiontext = request.POST.get('motiontext')
			motionname = request.POST.get('motionname')
			if motionname:
				motion = Motion(user=Account.objects.get(user=request.user), timestamp=datetime.now(), 
					name=motionname, desc=motiontext, likes=0, dislikes=0, pastname=motionname,
					pastdesc=motiontext, modded=False)
				motion.save()

				ai_id = request.POST.get('agendaid')
				modified_ai = AgendaItem.objects.get(id__exact=ai_id)
				modified_ai.motions.add(motion)
				modified_ai.save()

		if request.POST.get('comment'):
			comment = request.POST.get('comment')
			if comment:
				comment = Comment(user=Account.objects.get(user=request.user), timestamp=datetime.now(),
					text=comment, pasttext=comment, modded=False)
				comment.save()

				motion_id = request.POST.get('motionid')
				modified_motion = Motion.objects.get(id__exact=motion_id)
				modified_motion.comments.add(comment)
				modified_motion.save()

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
				message = 'Your motion "'+motion.name+'" in meeting "'+meeting.title+'" has been removed by a moderator.'
				mailgun_send(recipient, "Motion removed", message)
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
				message = 'Your comment on motion "'+motion.name+'" in meeting "'+meeting.title+'" has been removed by a moderator.'
				mailgun_send(recipient, "Comment removed", message)

			comment.modded = True
			comment.save()

	request.session['meeting_no'] = path
	request.session.modified=True

	context['m'] = meeting
	context['host'] = meeting.hosts.all()[0]
	agenda_items = meeting.agenda_items.order_by('number')

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
	if request.user.username != meeting.hosts.all()[0].user.username:
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
	if request.user.username != meeting.hosts.all()[0].user.username:
		return HttpResponseRedirect('..')

	context['meeting'] = meeting

	if request.method == 'POST':
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
				u = User.objects.filter(email=e)
				if u:
					account = Account.objects.get(user=u[0])
					meeting.members.add(account)
					account.meetings_in.add(meeting)
					meeting.save()
					account.save()
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
				u = User.objects.filter(email=e)
				if u:
					account = Account.objects.get(user=u[0])
					meeting.moderators.add(account)
					meeting.save()

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
		if c not in meeting.members.all() and c not in meeting.hosts.all():
			contacts.append(c)
	context['contacts'] = contacts

	return render_to_response('managemembers.html', context)

