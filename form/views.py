from django.http import HttpResponse
from django.shortcuts import render
from .models import Leads, Feeds
import logging
from django.conf import settings
from django.views.generic.base import HttpResponseRedirect
import datetime
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger('django')

def home(request):
    if Feeds.objects.all().count() == 0:
        Feeds().refresh_data()
    feeds = Feeds.objects.order_by('-hits').all()
    return render(request, 'form/index.html', {'feeds': feeds, 'email': request.COOKIES.get('email', '')})

def signup(request):
    leads = Leads()
    status = leads.insert_lead(request.POST['name'], request.POST['email'], request.POST['previewAccess'])
    response = HttpResponse('', status=status)
    expiry_date = datetime.datetime.utcnow() + datetime.timedelta(weeks=520)
    response.set_cookie('email', request.POST['email'], expires=expiry_date)
    return response

def hit(request, id):
    article = Feeds.objects.get(pk=id)
    article.hits += 1
    article.save()
    url_article = parse_qs(urlparse(article.link).query).get('url',['--missing--'])[0]
    url_hit = request.GET.get('url', '#')
    logger.info(f'[{url_article},{url_hit},{request.COOKIES.get('email')}]')
    return HttpResponseRedirect(redirect_to=url_hit)
