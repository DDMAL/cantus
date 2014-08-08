from django.contrib.auth.models import User
from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.serializers.user import UserSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
