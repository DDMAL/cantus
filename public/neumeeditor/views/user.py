from django.contrib.auth.models import User
from neumeeditor.serializers.user import UserSerializer
from rest_framework import generics


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
