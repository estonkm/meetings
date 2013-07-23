from django.core.management.base import NoArgsCommand
from data.models import *
from datetime import datetime
from pytz import timezone
from django.core.mail import send_mail
import pytz

ZONE = timezone('America/Chicago')
UTC = pytz.utc
SENDER = 'Vital Meeting <info@vitalmeeting.com>'
SIGNATURE = '\n\n\n\nVitalMeeting.com\nStructured Online Meetings'

class Command(NoArgsCommand):
	help = 'Checks meeting start/end times against current time'
	def handle_noargs(self, **options):
		meetings = Meeting.objects.all()
		now = ZONE.localize(datetime.now())

		for meeting in meetings:
			start = datetime.combine(meeting.startdate, meeting.starttime)
			end = datetime.combine(meeting.enddate, meeting.endtime)
			try:
				meetingtz = timezone(meeting.timezone)
			except:
				meetingtz = UTC

			start = meetingtz.localize(start)
			end = meetingtz.localize(end)
			now = now.astimezone(meetingtz)

			if (now - start).total_seconds() > 0 and meeting.started is False:
				meeting.started = True
				meeting.save()
				recipients = []
				for mem in meeting.members.all():
					e = mem.user.email
					recipients.append(e)
				title = 'Meeting Starting: '+meeting.title
				message = 'The meeting "'+meeting.title+'" is now open! Please visit http://vitalmeeting.com/meeting/'+meeting.meeting_id+' to join in.'+SIGNATURE
				send_mail(title, message, SENDER, recipients)
			if (now - end).total_seconds() >= 0 and meeting.ended is False:
				meeting.ended = True
				meeting.save()
				recipients = []
				for account in meeting.members.all():
					account.past_meetings.add(meeting)
					account.meetings_in.remove(meeting)
					account.save()
					e = account.user.email
					recipients.append(e)
				title = 'Meeting Ended: '+meeting.title
				message = 'The meeting "'+meeting.title+'" has ended.\n\n'
				for a in meeting.agenda_items.all():
					if a.motions.all():
						message += 'In agenda item "'+a.name+'", the most-liked was: "'+a.motions.all()[0]+'".\n\n'
				message += 'Please visit http://vitalmeeting.com/meeting/'+meeting.meeting_id+' to see the full results.'
				message += SIGNATURE

				send_mail(title, message, SENDER, recipients)


