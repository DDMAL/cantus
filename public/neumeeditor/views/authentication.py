from django.utils.datetime_safe import datetime
from rest_framework import status
from rest_framework.authentication import get_authorization_header
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.authtoken.models import Token


class ObtainExpiringAuthToken(ObtainAuthToken):
    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            token, created = Token.objects.get_or_create(user=serializer.object['user'])
            if not created:
                token.created = datetime.utcnow()
                token.save()
            return Response({'token': token.key},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != b'token':
            return Response({"status": "No token provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            return Response({"status": msg}, status=status.HTTP_400_BAD_REQUEST)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            return Response({"status": msg}, status=status.HTTP_400_BAD_REQUEST)
        # The token was provided, so we are going to delete it
        try:
            token = Token.objects.get(key=auth[1])
            token.delete()
            return Response({'status': "Token deleted.".format(auth[1])})
        except Token.DoesNotExist:
            return Response({"status": "Token does not exist."},
                            status=status.HTTP_401_UNAUTHORIZED)
