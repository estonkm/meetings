from data.models import *
from datetime import datetime

# class MyCronJob(CronJobBase):
# 	RUN_EVERY_MINS = 5

# 	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
# 	code = 'data.my_cron_job'

	# def do(self):
meetings = Meeting.objects.all()
now = datetime.now()

for meeting in meetings:
	start = datetime.combine(meeting.startdate, meeting.starttime)
	end = datetime.combine(meeting.enddate, meeting.endtime)

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
