from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Like(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
    )
    # 便于把前面两个信息合并
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'content_type', 'object_id'),)
        index_together = (('content_type', 'object_id', 'created_at'),)

    def __str__(self):
        return f'{self.created_at} - {self.user} liked {self.content_type} {self.object_id}'
