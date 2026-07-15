# blogs/views.py

import logging
import traceback

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

logger = logging.getLogger(__name__)

import os
from django.http import JsonResponse

def debug_env(request):
    return JsonResponse({
        "cloud_name": os.environ.get("CLOUDINARY_CLOUD_NAME"),
        "key_present": bool(os.environ.get("CLOUDINARY_API_KEY")),
        "secret_present": bool(os.environ.get("CLOUDINARY_API_SECRET")),
    })




class PostViewSet(viewsets.ModelViewSet):
    """
    GET    /api/blog/posts/            -> list published posts (public)
    GET    /api/blog/posts/?all=true   -> list ALL posts incl. drafts (admin only)
    GET    /api/blog/posts/<slug>/     -> single post detail
    POST   /api/blog/posts/            -> create post (admin only)
    PATCH  /api/blog/posts/<slug>/     -> update post (admin only)
    DELETE /api/blog/posts/<slug>/     -> delete post (admin only)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'list':
            if self.request.query_params.get('all') == 'true' and self.request.user.is_staff:
                return qs
            return qs.filter(is_published=True)
        return qs

    # ---- TEMPORARY DEBUG WRAPPER ----
    # Wraps list/create/update/destroy to catch and surface the real exception.
    # REMOVE this override once the bug is found and fixed.
    def handle_exception(self, exc):
        logger.error("Blog API exception: %s", exc, exc_info=True)
        tb = traceback.format_exc()
        print("==== BLOG API ERROR ====")
        print(tb)
        print("=========================")
        return Response(
            {
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": tb.splitlines()[-15:],  # last 15 lines, enough to see the cause
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )