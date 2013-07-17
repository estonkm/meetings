# builds timezone list for form usage - list of tuples
from pytz import all_timezones

def fillTZInfo():
	TIMEZONES = []

	for tz in all_timezones:
		TIMEZONES.append((tz, tz))
	return TIMEZONES

