from django.urls import path
from . import views

app_name = 'form'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup', views.signup, name='signup'),
    path("hit/<int:id>", views.hit, name="hit"),
]