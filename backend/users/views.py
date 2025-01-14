from rest_framework import views, generics, status, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import User
from .permissions import IsGuest, IsAuthenticatedUser, IsAdmin, IsAuthenticatedOrReadOnly
from .serializers import (
    UserSerializer, RegisterUserSerializer, AvatarSerializer, 
    PasswordResetSerializer, SubscriptionSerializer, SubscribeActionSerializer
)


class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RegisterUserSerializer
        return UserSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsGuest()]
        return [IsAuthenticatedOrReadOnly()]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CurrentUserView(views.APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AvatarUpdateView(views.APIView):
    permission_classes = [IsAuthenticatedUser]

    def put(self, request):
        serializer = AvatarSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetView(views.APIView):
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Пароль успешно изменен."}, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscribeView(views.APIView):
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        serializer = SubscribeActionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            target_user = serializer.save()
            return Response({"detail": f"Вы подписались на {target_user.username}."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedUser]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.subscriptions.all()