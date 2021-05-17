from testing.testcases import TestCase
from rest_framework.test import APIClient

LIKE_BASE_URL = '/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'
COMMENT_LIST_API = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


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

    def test_cancel(self):
        # jiapei created a tweet; jason created a comment under the tweet
        tweet = self.create_tweet(self.jiapei)
        comment = self.create_comment(self.jason, tweet)
        like_comment_data = {'content_type': 'comment', 'object_id': comment.id}
        like_tweet_data = {'content_type': 'tweet', 'object_id': tweet.id}

        # jiapei liked jason's comment; jason liked jiapei's tweet
        self.jiapei_client.post(LIKE_BASE_URL, like_comment_data)
        self.jason_client.post(LIKE_BASE_URL, like_tweet_data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # anonymous user is not valid
        response = self.anonymous_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 403)

        # get action is not allowed
        response = self.jiapei_client.get(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 405)

        # wrong content type
        response = self.jiapei_client.post(LIKE_CANCEL_URL, {
            'content_type': 'wrong type',
            'object_id': 1,
        })
        self.assertEqual(response.status_code, 400)

        # wrong object id
        response = self.jiapei_client.post(LIKE_CANCEL_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)

        # jason has not liked his own comment before
        # 静默处理
        response = self.jason_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # successfully canceled
        response = self.jiapei_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # jiapei has not liked jason's comment currently
        # 静默处理
        response = self.jiapei_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # jason's like to jiapei's tweet has been canceled
        response = self.jason_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 0)

    def test_likes_in_comments_api(self):
        tweet = self.create_tweet(self.jiapei)
        comment = self.create_comment(self.jason, tweet)

        # test anonymous
        response = self.anonymous_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)

        # test comments list api
        response = self.jason_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)
        # after jiapei liked this comment
        self.create_like(self.jiapei, comment)
        response = self.jiapei_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 1)

        # test tweet detail api
        # jason liked his own comment
        self.create_like(self.jason, comment)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.jason_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 2)

    def test_likes_in_tweets_api(self):
        tweet = self.create_tweet(self.jiapei)

        # test tweet detail api
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.jason_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['likes_count'], 0)
        # jason liked the tweet
        self.create_like(self.jason, tweet)
        response = self.jason_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['likes_count'], 1)

        # test tweets list api
        # get jiapei's tweet list
        response = self.jason_client.get(TWEET_LIST_API, {'user_id': self.jiapei.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tweets'][0]['has_liked'], True)
        self.assertEqual(response.data['tweets'][0]['likes_count'], 1)

        # test newsfeeds list api
        # jiapei liked his own tweet
        # jason created a newsfeed
        self.create_like(self.jiapei, tweet)
        self.create_newsfeed(self.jason, tweet)
        response = self.jason_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['has_liked'], True)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['likes_count'], 2)

        # test likes details
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.jason_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['likes']), 2)
        # ordered by created_at reversely
        self.assertEqual(response.data['likes'][0]['user']['id'], self.jiapei.id)
        self.assertEqual(response.data['likes'][1]['user']['id'], self.jason.id)
