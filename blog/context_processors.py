from .models import Category, Page, Post, Tag


def categories(request):
    """Оставьте, если используете all_categories где-то ещё."""
    return {'all_categories': Category.objects.all()}


def _build_menu(position):
    field = f'show_in_{position}'
    order_field = 'footer_order' if position == 'footer' else 'menu_order'
    items = []

    roots = (
        Category.objects
        .filter(**{field: True}, parent__isnull=True)
        .prefetch_related('children')
        .order_by('menu_order', 'name')
    )
    for cat in roots:
        children = [
            {
                'title': child.name,
                'url': child.get_absolute_url(),
            }
            for child in cat.children.filter(**{field: True}).order_by('menu_order', 'name')
        ]
        items.append({
            'title': cat.name,
            'url': cat.get_absolute_url(),
            'order': cat.menu_order,
            'kind': 'category',
            'children': children,
        })

    for page in Page.objects.filter(**{field: True}, is_published=True):
        items.append({
            'title': page.menu_label(),
            'url': page.get_absolute_url(),
            'order': page.menu_order,
            'kind': 'page',
            'children': [],
        })

    items.sort(key=lambda x: (x['order'], x['title'].lower()))
    return items


def menus(request):
    popular = (
        Post.published
        .filter(category__isnull=False, views__gt=0)
        .select_related('category')
        .order_by('-views')[:5]
    )
    active_tags = Tag.objects.filter(posts__is_published=True).distinct().order_by('name')
    return {
        'menu_header': _build_menu('header'),
        'menu_sidebar': _build_menu('sidebar'),
        'menu_footer': _build_menu('footer'),
        'popular_posts': popular,
        'all_tags': active_tags,
    }