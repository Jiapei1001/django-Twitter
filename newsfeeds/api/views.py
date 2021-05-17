from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed


class NewsFeedViewSet(viewsets.GenericViewSet):

    permission_classes = [IsAuthenticated]

    # override get_queryset method in GenericViewSet
    def get_queryset(self):
        # self defined queryset, because the authentication
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        # Update below to include context, to get likes count and comments count
        # serializer = NewsFeedSerializer(self.get_queryset(), many=True)
        serializer = NewsFeedSerializer(
            self.get_queryset(),
            context={'request': request},
            many=True,
        )

        return Response({
            'newsfeeds': serializer.data,
        }, status=200)
