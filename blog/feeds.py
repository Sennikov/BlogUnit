from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from martor.utils import markdownify
from django.utils.html import strip_tags
from .models import Post


class LatestPostsFeed(Feed):
    title = "Unitproglab — последние статьи"
    link = "/"
    description = "Блог о технологиях, разработке и IT-индустрии. Пишем просто о сложном."
    feed_type = Rss201rev2Feed
    feed_url = "/rss/"

    def items(self):
        return (
            Post.published
            .filter(is_published=True, category__isnull=False)
            .select_related('category')
            .order_by('-published_date')[:20]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        if item.meta_description:
            return item.meta_description

        from martor.utils import markdownify
        from django.utils.html import strip_tags
        html_content = markdownify(item.content)
        plain_text = strip_tags(html_content)
        text = plain_text[:400]
        if len(plain_text) > 400:
            text += '…'
        return text

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_date

    def item_author_name(self, item):
        return "Unitproglab"

    def item_categories(self, item):
        if item.category:
            return [item.category.name]
        return []