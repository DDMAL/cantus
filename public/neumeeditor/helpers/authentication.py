from django.contrib.auth import tokens
from django.utils.datetime_safe import datetime
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from datetime import timedelta
import pytz


class ExpiringTokenAuthentication(TokenAuthentication):

    max_age_days = 3

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

        if token.created < utc_now - timedelta(days=self.max_age_days):
            raise exceptions.AuthenticationFailed('Token has expired')
        return token.user, tokens


class ObtainExpiringAuthToken(ObtainAuthToken):
    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            token, created = Token.objects.get_or_create(user=serializer.object['user'])
            if not created:
                token.created = datetime.utcnow()
                token.save()
            return Response({'token': token.key})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
