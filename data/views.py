# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render_to_response
from django.template import RequestContext
from django.core.context_processors import csrf
from data.forms import MeetingForm, UserForm

def home(request):
	return render_to_response('index.html')

def create(request):
	context = {}
	context.update(csrf(request))
	form = MeetingForm(request.POST, request.FILES)
	context['form'] = form

	if request.method == 'POST':
		if request.POST.get('meetingsubmit'):
			if form.is_valid():
				cd = form.cleaned_data
				return HttpResponseRedirect('../signup')
			else:
				errors = {}
				context['errors'] = errors
				cd = form.cleaned_data

	return render_to_response('create.html', context)

def signup(request):
	return HttpResponseRedirect('..')

def meeting(request):
	return render_to_response('meeting_page.html')