from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from tweets.api.serializers import TweetSerializer, TweetCreateSerializer
from tweets.models import Tweet
from newsfeeds.services import NewsFeedService


class TweetViewSet(viewsets.GenericViewSet,
                   viewsets.mixins.CreateModelMixin,
                   viewsets.mixins.ListModelMixin):
    """
    API endpoint that allow users to create, list tweet
    """
    queryset = Tweet.objects.all()
    # 这个serializer_class只是为了在backend debug的UI界面里，POST时显示的表单是什么
    # 如果是serializer_class = TweetSerializer，那么需要多输入username
    # TweetCreateSerializer只是需要输入content
    # 完全只是UI界面
    serializer_class = TweetCreateSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        reload create method, because current login user as the tweet.user
        """
        serializer = TweetCreateSerializer(
            data=request.data,
            # 传递额外变量，request user把request整体进行传递
            context={'request': request},
        )

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=400)

        # 如何上面serializer里有instance，则对instance进行更新
        # 否则需要save()
        tweet = serializer.save()

        # 当增加推文时，自动推送到newsfeed之中
        NewsFeedService.fanout_to_followers(tweet)

        return Response(TweetSerializer(tweet).data, status=201)

    def list(self, request, *args, **kwargs):
        """
        reload list method, don't list all tweets, must use the user_id as the filter condition
        """
        if 'user_id' not in request.query_params:
            return Response('missing user_id', status=400)

        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')

        serializer = TweetSerializer(tweets, many=True)
        # 一般来说JSON格式的response，默认需要用hash的格式
        # 而不用list的格式（约定俗成）
        return Response({
            'tweets': serializer.data,
        })
