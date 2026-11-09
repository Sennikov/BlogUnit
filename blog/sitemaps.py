from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Category, Post, Page


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Post.published.filter(is_published=True, category__isnull=False)

    def lastmod(self, obj):
        return obj.published_date

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()


class PageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Post.published.filter(is_published=True)

    def lastmod(self, obj):
        return obj.published_date

    def location(self, obj):
        return obj.get_absolute_url()