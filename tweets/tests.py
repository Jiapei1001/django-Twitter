from django.test import TestCase
from datetime import timedelta
from utils.time_helpers import utc_now
from tweets.models import Tweet
from django.contrib.auth.models import User


class TweetTests(TestCase):

    def test_hours_to_now(self):
        jiapei = User.objects.create_user(username='Jiapei')
        tweet = Tweet.objects.create(user=jiapei, content='test time now')

        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()

        self.assertEqual(tweet.hours_to_now, 10)
