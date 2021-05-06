from django.db import models
from django.contrib.auth.models import User


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        # When on_delete=models.SET_NULL,
        # must have null=True
        null=True,
        # Redefine tweets = user.tweetSet.all(); tweets.objects.filter(from_user=user)
        # with the related_name, we can directly access the set by
        # user.following_friendship_set.all()
        related_name='following_friendship_set',
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='follower_friendship_set',
    )
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        index_together = (
            # get users I follow, order by created_at
            ('from_user_id', 'created_at'),
            # get users follow me, order by created_at
            ('to_user_id', 'created_at'),
        )
        # make sure one user cannot follow the other user twice
        unique_together = (('from_user_id', 'to_user_id'),)

    def __str__(self):
        # return '{} followed {}'.format(self.from_user, self.to_user)
        return f'{self.from_user} followed {self.to_user}'
