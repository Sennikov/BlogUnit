from django import template
from django.db.models import Q
from django.utils import timezone
from blog.models import AdBlock

register = template.Library()


@register.inclusion_tag('blog/_ad_list.html', takes_context=True)
def render_ads(context, position):
    now = timezone.now()
    qs = (
        AdBlock.objects
        .filter(position=position, is_active=True)
        .filter(Q(start_date__isnull=True) | Q(start_date__lte=now))
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=now))
        .order_by('order', 'title')
    )
    return {'ads': qs, 'position': position}