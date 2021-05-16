from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now

# NOTE: must add '/', or will trigger redirect 301
TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TweetApiTests(TestCase):

    def setUp(self):
        # Registered user
        self.user1 = self.create_user('user1', 'user1@gmail.com')
        self.tweets1 = [
            self.create_tweet(self.user1)
            for _ in range(3)
        ]

        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2', 'user2@gmail.com')
        self.tweets2 = [
            self.create_tweet(self.user2)
            for _ in range(2)
        ]

        self.jiapei = self.create_user('jiapei')
        self.tweet = self.create_tweet(self.jiapei)

    def test_list_api(self):
        # must request with user_id
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        # request successfully
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweets']), 3)
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(len(response.data['tweets']), 2)

        # test the ordering of responded tweets are in reverse order
        self.assertEqual(response.data['tweets'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['tweets'][1]['id'], self.tweets2[0].id)

    def test_create_api(self):
        # must login
        response = self.anonymous_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 403)

        # must have field of content
        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)

        # content cannot be too short
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        # content cannot be too long
        response = self.user1_client.post(TWEET_CREATE_API, {'content': '0'*141})
        self.assertEqual(response.status_code, 400)

        # post successfully
        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'Is this my first tweet? Yes!'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count + 1)

    def test_retrieve(self):
        # tweet with id=-1 doesn't exist
        url = TWEET_RETRIEVE_API.format(-1)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 404)

        # when retrieve a tweet, the returned data also comes with comments
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        self.create_comment(self.user2, tweet, 'user2 commented on the just created tweet')
        self.create_comment(self.user1, tweet, 'hmmmmmm....hello!')
        response = self.anonymous_client.get(url)
        self.assertEqual(len(response.data['comments']), 2)

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.jiapei, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.jiapei, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        jason = self.create_user('jason')
        self.create_like(jason, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)
