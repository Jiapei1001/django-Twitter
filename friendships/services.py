from friendships.models import Friendship

class FriendshipService(object):

    @classmethod
    def get_followers(cls, user):
        # WRONG #1 : access database Q + 1 times
        # friendships = Friendship.objects.filter(to_user=user)
        # return [friendship.from_user for friendship in friendships]

        # WRONG #2 : JOIN operation, by joining two tables
        # slow, not used in web application
        # friendships = Friendship.objects.filter(
        #     to_user==user
        # ).select_related('from_user')
        # return [friendship.from_user for friendship in friendships]

        # CORRECT : similar as the "prefetch_related" method as below
        # friendships = friendships = Friendship.objects.filter(to_user=user)
        # follower_ids = [friendship.from_user_id in friendship in friendships]
        # followers = User.objects.filter(id__in=follower_ids)

        friendships = Friendship.objects.filter(
            to_user=user,
        ).prefetch_related('from_user')

        return [friendship.from_user for friendship in friendships]