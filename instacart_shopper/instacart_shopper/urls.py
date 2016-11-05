from django.conf.urls import url

from . import views

app_name = 'instacart_shopper'
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^register/$', views.register, name='register'),
    url(r'^confirmation/$', views.confirmation, name='confirmation'),
    url(r'^edit/$', views.edit, name='edit'),
    url(r'^update/$', views.update, name='update'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^login/$', views.login, name='login'),  
    url(r'^seed_data/(?P<count>.*)/$', views.insert_seed_data, name='insert_seed_data'),
    url(r'^funnel.json/$', views.funnel_metrics, name='funnel_metrics')
]