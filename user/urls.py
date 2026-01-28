from django.urls import path
from . import apis

urlpatterns = [
    path('send-sms/', apis.send_test_sms, name='send-sms'),
]