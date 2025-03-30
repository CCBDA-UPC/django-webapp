from django.http import HttpResponse
from django.shortcuts import render
from .models import Leads
import logging
from django.conf import settings

logger = logging.getLogger('django')

def home(request):
    return render(request, 'form/index.html')


def signup(request):
    leads = Leads()
    status = leads.insert_lead(request.POST['name'], request.POST['email'], request.POST['previewAccess'])
    return HttpResponse('', status=status)
