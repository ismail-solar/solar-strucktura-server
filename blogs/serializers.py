from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "image",
            "image_alt",
            "description",
            "content",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']