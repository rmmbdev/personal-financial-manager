import datetime

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# Create your views here.
class HelloView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = request.data
        content = {"message": "Hi {}".format(request.user.username)}
        return Response(content)


class ObtainExpiringAuthToken(ObtainAuthToken):
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token, created = Token.objects.get_or_create(user=serializer.validated_data['user'])
            token.delete()
            token = Token.objects.create(user=token.user)
            token.created = datetime.datetime.utcnow()
            token.save()
            return Response({'token': token.key})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


obtain_expiring_auth_token = ObtainExpiringAuthToken.as_view()
