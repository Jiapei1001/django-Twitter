from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship

NEWSFEED_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'

class NewsFeedApiTest(TestCase):

    def setUp(self):

        self.jiapei = self.create_user('jiapei')
        self.jiapei_client = APIClient()
        self.jiapei_client.force_authenticate(self.jiapei)

        self.jason = self.create_user('jason')
        self.jason_client = APIClient()
        self.jason_client.force_authenticate(self.jason)

        # create followers
        for i in range(2):
            follower = self.create_user('jiapei_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.jiapei)

        # create followings
        for i in range(3):
            following = self.create_user('jiapei_following{}'.format(i))
            Friendship.objects.create(from_user=self.jiapei, to_user=following)

    def test_list(self):

        # need to login
        response = self.anonymous_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 403)

        # cannot use POST
        response = self.jiapei_client.post(NEWSFEED_URL)
        self.assertEqual(response.status_code, 405)

        # there is nothing in the list initially
        response = self.jiapei_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)

        # the user himself can see tweet the he just sent and fanouted
        self.jiapei_client.post(POST_TWEETS_URL, {'content' : 'The very first tweet to fanout!'})
        response = self.jiapei_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 1)

        # after jiapei followed jason, jiapei can see the new tweet jason just sent
        self.jiapei_client.post(FOLLOW_URL.format(self.jason.id))
        response = self.jason_client.post(POST_TWEETS_URL, {
            'content': 'Hello Twitter from Jason!'
        })
        posted_tweet_id = response.data['id']
        response = self.jiapei_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        # jiapei formerly sent one tweet himself
        # thus, there are two tweets in jiapei's newsfeed
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)
