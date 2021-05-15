from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from friendships.api.serializers import (
    FollowerSerializer,
    FollowingSerializer,
    FriendshipSerializerForCreate,
)
from django.contrib.auth.models import User
from friendships.models import Friendship


class FriendshipViewSet(viewsets.GenericViewSet):

    # NOTE: here is not Friendship.objects.all(), or will get 404 error
    queryset = User.objects.all()

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
        # many=True, then the returned result is a list
        serializer = FollowerSerializer(friendships, many=True)
        return Response({
            'followers': serializer.data,
        }, status=200)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')
        serializer = FollowingSerializer(friendships, many=True)
        return Response({
            'followings': serializer.data,
        }, status=200)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        # avoid duplicated follow actions
        # ????为什么这里是to_user，而不是to_user_id???
        if Friendship.objects.filter(from_user=request.user, to_user=pk).exists():
            return Response({
                'success': True,
                'duplicate': True,
            }, status=201)

        serializer = FriendshipSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': pk,
        })

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
            }, status=400)

        serializer.save()
        return Response({
            'success': True,
        }, status=201)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        # NOTE: pk type is string; need to change its type
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'message': 'You cannot unfollow yourself',
            }, status=400)

        # Queryset's delete method will return two values, one as how many data got delete,
        # the other one as how many data got deleted in specific type
        # the second one is driven by on_delete=models.CASCADE
        # then the two tables have the life cycle dependency

        # ??? 为什么这里不是from_user_id，和to_user_id???
        deleted, _ = Friendship.objects.filter(
            from_user=request.user,
            to_user=pk,
        ).delete()

        return Response({
            'success': True,
            'deleted': deleted,
        })
