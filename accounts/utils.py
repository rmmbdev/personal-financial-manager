import datetime as dtime
from datetime import datetime

import pytz
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token')  # Exceptions.AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise AuthenticationFailed(
                'User inactive or deleted')  # exceptions.AuthenticationFailed('User inactive or deleted')

        # This is required for the time comparison
        utc_now = datetime.now(dtime.timezone.utc)
        utc_now = utc_now.replace(tzinfo=pytz.utc)

        if token.created < utc_now - settings.TOKEN_EXPIRE_TIME:
            raise AuthenticationFailed('Token has expired')  # exceptions.AuthenticationFailed('Token has expired')

        return token.user, token
