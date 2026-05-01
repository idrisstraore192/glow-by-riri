
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from shop.sitemaps import StaticSitemap, ProductSitemap

sitemaps = {
    'static': StaticSitemap,
    'products': ProductSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("shop/", include("shop.urls")),
    path("booking/", include("booking.urls")),
    path("avis/", include("reviews.urls")),
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", lambda r: HttpResponse(
        "User-agent: *\nAllow: /\nSitemap: https://glowbyriri.store/sitemap.xml\n",
        content_type="text/plain"
    )),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
