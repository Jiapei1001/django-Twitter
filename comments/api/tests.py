from testing.testcases import TestCase
from rest_framework.test import APIClient
from comments.models import Comment
from django.utils import timezone


COMMENT_URL = '/api/comments/'
TWEET_LIST_URL = '/api/tweets/'
TWEET_DETAIL_URL = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class CommentApiTests(TestCase):
    def setUp(self):
        self.jiapei = self.create_user('jiapei')
        self.jiapei_client = APIClient()
        self.jiapei_client.force_authenticate(self.jiapei)

        self.jason = self.create_user('jason')
        self.jason_client = APIClient()
        self.jason_client.force_authenticate(self.jason)

        self.tweet = self.create_tweet(self.jiapei)
        # self.comment = self.create_comment(self.jiapei, self.tweet)

    def test_create(self):
        # anonymous user cannot create comment
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # no comment content
        response = self.jiapei_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # cannot post with only tweet id
        response = self.jiapei_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # cannot post with only content
        response = self.jiapei_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        # content too long
        response = self.jiapei_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1' * 141,
        })
        self.assertEqual(response.status_code, 400)

        # valid post
        response = self.jiapei_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.jiapei.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')

    def test_update(self):
        comment = self.create_comment(self.jiapei, self.tweet, 'first comment test')
        another_tweet = self.create_tweet(self.jason)
        url = f'{COMMENT_URL}{comment.id}/'

        # cannot update for an anonymous user
        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)

        # cannot update if not object's owner
        response = self.jason_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')

        # cannot update anything else other than the comment's content
        # 静默处理
        before_created_at = comment.created_at
        before_updated_at = comment.updated_at
        now = timezone.now()
        response = self.jiapei_client.put(url, {
            'content': 'new',
            # should be jiapei.id
            'user_id': self.jason.id,
            # should be original tweet's id
            'tweet_id': another_tweet.id,
            # should be former time
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.jiapei)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        # updated_at has been updated
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list(self):
        # must have tweet_id
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # can access
        # no comment in the tweet
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # comments are sorted by created_at in increasingly sequential order
        self.create_comment(self.jiapei, self.tweet, '1')
        self.create_comment(self.jason, self.tweet, '2')
        self.create_comment(self.jason, self.create_tweet(self.jason), '3')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # provide both user_id and tweet_id
        # only tweet_id will be effective in filtering the comments
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.jiapei.id,
        })
        self.assertEqual(len(response.data['comments']), 2)

    def test_like_set(self):
        self.create_like(self.jiapei, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.jiapei, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.jason, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_comments_count(self):
        # test tweet detail api
        tweet = self.create_tweet(self.jiapei)
        url = TWEET_DETAIL_URL.format(tweet.id)

        response = self.jason_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # test tweet list api
        self.create_comment(self.jiapei, tweet)
        # get jiapei's tweet list
        response = self.jason_client.get(TWEET_LIST_URL, {'user_id': self.jiapei.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tweets'][0]['comments_count'], 1)

        # test newsfeed list api
        self.create_comment(self.jason, tweet)
        self.create_newsfeed(self.jason, tweet)
        response = self.jason_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['comments_count'], 2)
