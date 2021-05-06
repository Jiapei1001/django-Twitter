from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from tweets.models import Tweet


class TestCase(DjangoTestCase):

    def create_user(self, username, email, password=None):
        if password is None:
            password = 'generic password'

        # 不能直接User.objects.create()
        # 因为password需要加密，同时username和email需要normalize处理
        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'

        return Tweet.objects.create(user=user, content=content)
