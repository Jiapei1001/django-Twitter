from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed

class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        # WRONG : Never use FOR loop to query database!!
        # N + 1 queries
        # for follower in FriendshipService.get_followers(tweet.user):
        #     NewsFeed.objects.create(
        #         user=tweet.user,
        #         tweet=tweet
        #     )

        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in FriendshipService.get_followers(tweet.user)
        ]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))

        # BULK CREATE, will decrease the amount of queries to the database
        NewsFeed.objects.bulk_create(newsfeeds)
