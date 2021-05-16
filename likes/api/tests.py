from testing.testcases import TestCase


LIKE_BASE_URL = '/api/likes/'


class likeApiTests(TestCase):

    def setUp(self):
        self.jiapei, self.jiapei_client = self.create_user_and_client('jiapei')
        self.jason, self.jason_client = self.create_user_and_client('jason')

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.jiapei)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        # anonymous client is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.jiapei_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # post successfully
        response = self.jiapei_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)

        # duplicated likes
        # 静默处理
        self.jiapei_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.jason_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.jiapei)
        comment = self.create_comment(self.jason, tweet)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # anonymous client is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.jiapei_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # wrong content type
        response = self.jiapei_client.post(LIKE_BASE_URL, {
            # comment is spelled wrong, with a less of 'm'
            'content_type': 'coment',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object id
        response = self.jiapei_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # post successfully
        response = self.jiapei_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicated likes
        # 静默处理
        response = self.jiapei_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)
        self.jason_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)
