from django.urls import path, re_path

from . import views

app_name = 'form'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup', views.signup, name='signup'),
]