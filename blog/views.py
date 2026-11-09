from django.contrib.admin.templatetags.admin_list import pagination
from django.http import Http404
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Category, Post, Page, Draft, AdBlock, Tag
from django.db.models import Q
from django.shortcuts import render
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone




def home(request):
    category = Category.objects.all()
    post_qs = (
        Post.published
        .filter(is_published=True,category__isnull=False)
        .select_related('category', 'category__parent')
        .order_by('-published_date')
    )
    paginator = Paginator(post_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/home.html',{
        'category':category,
        'page_obj': page_obj,
    })


def slug_detail(request, slug):
    # 1. Пытаемся найти категорию по слагу
    category = Category.objects.select_related('parent').filter(slug=slug).first()
    if category:
        ids = category.descendants_ids()
        posts_qs = (
            Post.published
            .filter(category_id__in=ids, is_published=True)
            .select_related('category')
            .order_by('-published_date')
        )
        paginator = Paginator(posts_qs, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        subcategories = category.children.all()

        return render(request, 'blog/category_detail.html', {
            'category': category,
            'subcategories': subcategories,
            'page_obj': page_obj,
        })

    # 2. Если категории нет, ищем страницу (пост без категории)
    page = Page.objects.filter(slug=slug, is_published=True, published_date__lte=timezone.now()).first()
    if page:
        return render(request, 'blog/post_detail.html', {'post': page})

    # 3. Ничего не нашли — 404
    raise Http404("Страница не найдена")

def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts_qs = (
        Post.published
        .filter(is_published=True, category__isnull=False, tags=tag)
        .select_related('category')
        .order_by('-published_date')
    )
    paginator = Paginator(posts_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'blog/tag_detail.html', {
        'tag': tag,
        'page_obj': page_obj,
    })

def _related_posts(post,limit=6):
    """
    Похожие статьи: та же категория, кроме текущей.
    Сортируем по просмотрам и дате. Если мало — берём из соседних категорий.
    """
    if not post.category_id:
        return Post.objects.none()
    base_qs = (
        Post.published
        .filter(is_published=True)
        .exclude(pk=post.pk)
        .select_related('category')
    )
    # 1. Та же категория
    same = list(
        base_qs
        .filter(category_id=post.category_id)
        .order_by('-views', '-published_date')[:limit]
    )

    if len(same) >= limit:
        return same[:limit]

    # 2. Родительская категория и её дети (если мало)
    siblings = []
    if post.category.parent_id:
        sibling_ids = (
            Category.objects
            .filter(parent_id=post.category.parent_id)
            .exclude(pk=post.category_id)
            .values_list('id', flat=True)
        )
        siblings = list(
            base_qs
            .filter(category_id__in=sibling_ids)
            .exclude(pk__in=[p.pk for p in same])
            .order_by('-views', '-published_date')[:limit - len(same)]
        )

    # 3. Всё остальное (крайний случай, если совсем мало)
    result = same + siblings
    if len(result) < limit:
        fallback = list(
            base_qs
            .exclude(pk__in=[p.pk for p in result])
            .order_by('-views', '-published_date')[:limit - len(result)]
        )
        result += fallback

    return result[:limit]


def post_detail(request, category_slug, post_slug):
    post = get_object_or_404(
        Post.objects.select_related('category', 'category__parent'),
        slug=post_slug,
        category__slug=category_slug,
        is_published = True,
    )

    viewed_key = f'viewe_post_{post.pk}'
    if not request.session.get(viewed_key):
        Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
        post.refresh_from_db(fields=['views'])
        request.session[viewed_key] = True

    related = _related_posts(post, limit=6)

    return render(request, 'blog/post_detail.html',{'post':post, 'related_posts': related,})

# def page_detail(request, post_slug):
#     page = get_object_or_404(Page, slug= post_slug, is_published = True)
#     return  render(request, 'blog/post_detail.html', {'post': page})

#Поиск по сайту.

def search(request):
    query = request.GET.get('q', '').strip()
    posts = Post.objects.none()

    if query:
        posts = Post.published.filter(
            Post.objects
            .filter(is_published=True, category__isnull=False)
            .filter(Q(title__icontains=query) | Q(content__icontains=query))
            .select_related('category')
            .order_by('-published_date')
        )

    return render(request, 'blog/search_results.html', {
        'query': query,
        'posts': posts,
    })


# ============================================================
#  РЕКЛАМА: КЛИКИ И ПОКАЗЫ
# ============================================================
def ad_click(request, pk):
    ad = get_object_or_404(AdBlock, pk=pk, is_active=True)
    AdBlock.objects.filter(pk=pk).update(clicks=F('clicks') + 1)
    if ad.url:
        return HttpResponseRedirect(ad.url)
    return HttpResponseRedirect('/')


def ad_impression(request, pk):
    AdBlock.objects.filter(pk=pk, is_active=True).update(impressions=F('impressions') + 1)
    # Прозрачный GIF 1×1
    return HttpResponse(
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff'
        b'\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x44\x01\x00\x3b',
        content_type='image/gif',
    )