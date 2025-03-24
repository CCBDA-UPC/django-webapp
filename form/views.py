from django.http import HttpResponse
from django.shortcuts import render
from .models import Leads
from django.conf import settings
import logging

def home(request):
    logging.error(f'ALLOWED_HOSTS {settings.ALLOWED_HOSTS}')
    return render(request, 'form/index.html')


def signup(request):
    leads = Leads()
    status = leads.insert_lead(request.POST['name'], request.POST['email'], request.POST['previewAccess'])
    return HttpResponse('', status=status)
