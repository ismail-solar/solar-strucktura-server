 
from django.contrib import admin
from django.urls import path,include

from blogs.views import debug_env
from my_site.views import home
from django.contrib.sitemaps.views import sitemap

from .sitemap import (
    StaticViewSitemap,
    BlogSitemap,
)

sitemaps = {
    "static": StaticViewSitemap,
    "blog": BlogSitemap,
}

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path('api/', include('accounts.urls')),
    path('plans/', include('plans.urls')),
    path("invoices/", include("invoices.urls")),
    path("projects/", include("projects.urls")),
    path('api/blog/', include('blogs.urls')),
    # path('api/debug-env/', debug_env),  #for testing secrets
    path("sitemap.xml",sitemap,{"sitemaps": sitemaps},),
    
]