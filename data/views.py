# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render_to_response
from django.template import RequestContext

def home(request):
	return render_to_response('index.html')