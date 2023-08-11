from django.urls import path

from .views import *

urlpatterns = [
    path('hello/', HelloView.as_view(), name='hello'),
    path('api-token-auth/', obtain_expiring_auth_token, name='api_token_auth_expiring')
]
