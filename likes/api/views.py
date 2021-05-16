from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from twitter.decorators import required_params
from likes.models import Like
from likes.api.serializers import (
    LikeSerializer,
    LikeSerializerForCreate,
)


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = LikeSerializerForCreate

    @required_params(request_attr='data', params=['content_type', 'object_id'])
    def create(self, request, *args, **kwargs):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        return Response(
            # NOTE: when use serializer to operate data,
            # here don't need to wrap the serializer.data with {}
            # if {} is added, it will trigger error here, as below:
            # TypeError: unhashable type: 'ReturnDict'
            LikeSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )
