from django import template
from blog.utils import get_git_info

register = template.Library()

@register.simple_tag
def get_git_status():
    return get_git_info()