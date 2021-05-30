from accounts.api.serializers import UserSerializer
from comments.models import Comment
from tweets.models import Tweet
from likes.models import Like
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Like
        fields = ('user', 'created_at')


class BaseLikeSerializerForCreateAndCancel(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(choices=['tweet', 'comment'])
    object_id = serializers.IntegerField()

    class Meta:
        model = Like
        fields = ('content_type', 'object_id')

    def _get_model_class(self, data):
        if data['content_type'] == 'comment':
            return Comment
        if data['content_type'] == 'tweet':
            return Tweet
        return None

    def validate(self, data):
        model_class = self._get_model_class(data)
        if model_class is None:
            raise ValidationError({
                'content_type': 'Content type does not exist.'
            })
        liked_object = model_class.objects.filter(id=data['object_id']).first()
        if liked_object is None:
            raise ValidationError({
                'object_id': 'Object does not exist.'
            })
        return data


class LikeSerializerForCreate(BaseLikeSerializerForCreateAndCancel):
    # def create(self, validated_data):
    #     model_class = self._get_model_class(validated_data)
    #     instance, _ = Like.objects.get_or_create(
    #         # need to deliver the context
    #         user=self.context['request'].user,
    #         content_type=ContentType.objects.get_for_model(model_class),
    #         object_id=validated_data['object_id'],
    #     )
    #     return instance

    # after adding Notifications:
    # See LikeViewSet, check if it is created, and avoid duplication.
    def get_or_create(self):
        model_class = self._get_model_class(self.validated_data)
        return Like.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=self.validated_data['object_id'],
            user_id=self.context['request'].user,
        )


class LikeSerializerForCancel(BaseLikeSerializerForCreateAndCancel):
    # cancel is a self-defined method, it is not like create -> serializer.save()
    # must use serializer.cancel()
    def cancel(self):
        model_class = self._get_model_class(self.validated_data)
        Like.objects.filter(
            user=self.context['request'].user,
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=self.validated_data['object_id'],
        ).delete()
