from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blogs.models import Post

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"
    def items(self):
        return [
            "home",
            "pricing",
            "services",
            "contact",
            "blog",
        ]

    def location(self, item):
        return reverse(item)
    
class BlogSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8
    def items(self):
        return Post.objects.filter(is_published=True)
    def lastmod(self, obj):
        return obj.updated_at
    def location(self, obj):
        return f"/blog/{obj.slug}"