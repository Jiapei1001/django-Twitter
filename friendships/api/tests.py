from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

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

    def test_follow(self):
        url = FOLLOW_URL.format(self.jiapei.id)

        # must login
        # response = self.anonymous_client.get(url)
        # print(response)
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # must use POST method
        response = self.jason_client.get(url)
        self.assertEqual(response.status_code, 405)

        # cannot follow himself
        response = self.jiapei_client.post(url)
        self.assertEqual(response.status_code, 400)

        # follow successfully
        response = self.jason_client.post(url)
        self.assertEqual(response.status_code, 201)

        # follow again, default as successfully
        response = self.jason_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)

        # a new data will be added if a counter following process is added
        count = Friendship.objects.count()
        response = self.jiapei_client.post(FOLLOW_URL.format(self.jason.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.jiapei.id)

        # must login
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # cannot use GET
        response = self.jason_client.get(url)
        self.assertEqual(response.status_code, 405)

        # cannot unfollow himself
        response = self.jiapei_client.post(url)
        self.assertEqual(response.status_code, 400)

        # unfollow successfully
        Friendship.objects.create(from_user=self.jason, to_user=self.jiapei)
        count = Friendship.objects.count()
        response = self.jason_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Friendship.objects.count(), count - 1)
        self.assertEqual(response.data['deleted'], 1)

        # in the unfollow condition, when unfollow, nothing happens
        count = Friendship.objects.count()
        response = self.jason_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Friendship.objects.count(), count)
        self.assertEqual(response.data['deleted'], 0)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.jiapei.id)

        # POST method is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # GET is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)

        # make sure the ordering is reverse
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'jiapei_following2'
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'jiapei_following1'
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'jiapei_following0'
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.jiapei.id)

        # POST method is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # GET is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)

        # make sure the ordering is reverse
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'jiapei_follower1'
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'jiapei_follower0'
        )
