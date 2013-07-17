from django.core.management.base import NoArgsCommand
from data.models import *
from datetime import datetime
from pytz import timezone
import pytz

class Command(NoArgsCommand):
	help = 'Checks meeting start/end times against current time'
	def handle_noargs(self, **options):
		meetings = Meeting.objects.all()
		now = datetime.now()
		utc = pytz.utc
		now = utc.localize(now)

		for meeting in meetings:
			start = datetime.combine(meeting.startdate, meeting.starttime)
			end = datetime.combine(meeting.enddate, meeting.endtime)
			start = utc.localize(start)
			end = utc.localize(end)

			if (now - start).total_seconds() > 0:
				meeting.started = True
				meeting.save()
			if (now - end).total_seconds() > 0:
				meeting.ended = True
				meeting.save()
				for account in meeting.members.all():
					account.past_meetings.add(meeting)
					account.meetings_in.remove(meeting)
					account.save()
				for account in meeting.hosts.all():
					account.past_meetings.add(meeting)
					account.meetings_in.remove(meeting)
					account.save()
