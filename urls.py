from django.conf.urls import patterns, url
from rudi import views


urlpatterns = patterns(
    "rudi",
    url(r'^$', views.registration, name="registration"),
    url(r'^confirm/(?P<code>[a-zA-Z0-9]+)/$',
        views.confirm_email, name="confirm"),
)
