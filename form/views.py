from django.http import HttpResponse
from django.shortcuts import render, reverse
from .models import Leads, Feeds
import feedparser
import requests
import logging
from django.views.generic.base import HttpResponseRedirect
import urllib

rss_urls = [
    'https://www.cloudcomputing-news.net/feed/',
    'https://feeds.feedburner.com/cioreview/fvHK',
    'https://www.techrepublic.com/rssfeeds/topic/cloud/',
    'https://aws.amazon.com/blogs/aws/feed/',
    'https://cloudtweaks.com/feed/',
]
if Feeds.objects.all().count() == 0:
    for u in rss_urls:
        response = requests.get(u)
        try:
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                link = entry.link
                id = 5
                new_link = urllib.urlencode(reverse('form:hit', {'id':id}),{'url':urllib.parse.urlencode(link)})

                article = Feeds.objects.create(
                    title=entry.title,
                    link=entry.link,
                    summary='',
                    author=entry.author
                )
                article.summary = entry.summary.replace(link,new_link)
                article.save()
                print(entry.title)
        except Exception as e:
            logging.error(f'Feed reading error: {e}')

def hit(request, id):
    article = Feeds.objects.get(pk=id)
    article.hits += 1
    article.save()
    return HttpResponseRedirect(redirect_to=request.GET.get('url','#'))
def home(request):
    feeds = Feeds.objects.order_by('-hits').all()
    return render(request, 'form/index.html', {'feeds': feeds})


def signup(request):
    leads = Leads()
    status = leads.insert_lead(request.POST['name'], request.POST['email'], request.POST['previewAccess'])
    return HttpResponse('', status=status)
