from email.policy import default

from django.contrib import admin
from unicodedata import category
from .models import Category, Post, Page, Draft, AdBlock, SiteSettings, Tag
from django.utils import timezone
from django.utils.html import format_html
# admin.site.register(Post,Category)
from admin_extra_buttons.api import ExtraButtonsMixin, button
from django.urls import reverse
from django.shortcuts import redirect
from .utils import get_git_info

# Register your models here.

# @admin.register(Category)
#
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name','slug')
#     prepopulated_fields = {'slug':('name',)}
#     search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug','show_in_header', 'show_in_sidebar', 'menu_order', 'footer_order','show_in_footer')
    list_editable = ('show_in_header', 'show_in_sidebar', 'menu_order','footer_order', 'show_in_footer',)
    list_filter = ('parent', 'show_in_header', 'show_in_sidebar','show_in_footer')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_select_related = ('parent',)
    autocomplete_fields = ('parent',)    # удобный поиск родителя

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('preview_thumb','title','get_category','created_date', 'views', 'published_date', 'is_published','slug')
    list_display_links = ('title',)
    list_filter = ('category','is_published')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_date'
    list_editable = ('is_published',)



    # @button(
    #     label='🔄 Обновить блог с GitHub',
    #     change_form=False,
    #     change_list=True,
    #     permission='superuser',  # Только суперпользователь
    #     html_attrs={'style': 'background-color: #417690; color: white; font-weight: bold;'}
    # )
    # def update_from_git(self, request):
    #     from django.urls import reverse
    #     from django.shortcuts import redirect
    #     return redirect(reverse('blog:admin_deploy'))
    #
    # # 2. Отображение версии и статуса (текст над кнопками)
    #     def changelist_view(self, request, extra_context=None):
    #         extra_context = extra_context or {}
    #
    #     try:
    #         git_info = get_git_info()
    #     except Exception as e:
    #         git_info = {'error': str(e), 'version': 'unknown', 'update_available': False}
    #
    #     # Определяем цвет и текст статуса
    #     if git_info.get('error'):
    #         status_text = f"⚠️ Ошибка Git: {git_info.get('error')}"
    #         status_color = '#dc3545' # Красный
    #     elif git_info.get('update_available'):
    #         status_text = f"🔔 Доступно обновление! Текущая версия: {git_info.get('version', 'unknown')}"
    #         status_color = '#ffc107' # Оранжевый
    #     else:
    #         status_text = f"✅ Версия {git_info.get('version', 'unknown')} актуальна."
    #         status_color = '#28a745' # Зеленый
    #
    #     extra_context['git_status'] = {
    #         'text': status_text,
    #         'color': status_color,
    #         'branch': git_info.get('branch', 'unknown')
    #     }
    #
    #     return super().changelist_view(request, extra_context=extra_context)

    #URL (SLUG) Заполняется автоматически у статей, пользователь не должен его менять.
    readonly_fields = ('slug','preview_preview')
    filter_horizontal = ('tags',)
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'category','tags', 'content', 'preview'),
        }),
        ('Публикация', {
            'fields': ('is_published', 'published_date'),'description': 'Если вы укажете будущую дату, статья автоматически появится на сайте только в это время.',
        }),
        ('SEO', {
            'fields': ('seo_title','meta_description',),
            'description': 'Заполните для красивых сниппетов в поиске и соцсетях.'
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(category__isnull=False)


    @admin.display(description='Превью')
    def preview_thumb(self, obj):
        if obj.preview:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;" />',
                obj.preview.url,
            )
        return '-'

    @admin.display(description='Предпросмотр')
    def preview_preview(self, obj):
        if obj.preview:
            return format_html(
                '<img src="{}" style="max-width:400px;border-radius:6px;" />',
                obj.preview.url,
            )
        return 'Изображение не загружено'

    # Описываем метод, который красиво выведет категории
    @admin.display(description='Категории')  # Это добавит заголовок колонки
    def get_category(self, obj):
        if not obj.category:
            return '-'
        return obj.category.name
        # return ', '.join(c.name for c in obj.category.all())

    #@admin.display(boolean=True, description='Опубликовано')
    #def is_published(self, obj):
       # return obj.published_date is not None

    @admin.action(description='Опубликовать выбранные статьи')
    def make_published(self, request, queryset):
        queryset.update(is_published=True, published_date = timezone.now())

    @admin.action(description='Снять с публикации выбранные статьи')
    def make_unpublished(self, request, queryset):
        queryset.update(is_published=False)
    actions = [make_published, make_unpublished]



@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'slug',
        'show_in_header', 'show_in_sidebar', 'show_in_footer',
        'menu_order', 'footer_order',
    )
    list_editable = (
        'show_in_header', 'show_in_sidebar', 'show_in_footer',
        'menu_order', 'footer_order',
    )
    list_filter = ('show_in_header', 'show_in_sidebar', 'show_in_footer')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    filter_horizontal = ('tags',)
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'content', 'tags','preview'),
        }),
        ('Публикация', {
            'fields': ('is_published', 'published_date'),
        }),
        ('SEO', {
            'fields': ('seo_title','meta_description',),
            'description': 'Заполните для красивых сниппетов в поиске и соцсетях.'
        }),
        ('Меню', {
            'fields': (
                'menu_title',
                'show_in_header', 'show_in_sidebar', 'show_in_footer',
                'menu_order', 'footer_order',
            ),
            'description': 'Отметьте, где показывать страницу, и задайте порядок в каждом меню.',
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.category = None
        super().save_model(request, obj, form, change)


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_date', 'slug')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'category', 'tags', 'content', 'preview'),
            'description': (
                'Вы пишете черновик. Категорию можно выбрать сейчас — '
                'тогда материал переедет в раздел «Статьи». '
                'Или оставьте пустой и опубликуйте — станет «Страницей».'
            ),
        }),
        ('Публикация', {
            'fields': ('is_published', 'published_date'),
            'description': 'Поставьте «Опубликовано», чтобы перенести материал в «Статьи» или «Страницы».',
        }),
        ('SEO', {
            'fields': ('seo_title','meta_description',),
            'description': 'Заполните для красивых сниппетов в поиске и соцсетях.'
        }),
    )



@admin.register(AdBlock)
class AdBlockAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'position', 'type', 'is_active', 'order',
        'impressions', 'clicks',
    )
    list_editable = ('position', 'is_active', 'order')
    list_filter = ('position', 'type', 'is_active')
    search_fields = ('title', 'text', 'url')
    list_per_page = 30

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'position', 'type', 'is_active', 'order'),
        }),
        ('Текстовая реклама', {
            'fields': ('text',),
            'description': 'Заполняется, если тип = «Текстовая реклама».',
        }),
        ('Баннер', {
            'fields': ('image', 'image_alt'),
            'description': 'Заполняется, если тип = «Баннер».',
        }),
        ('Рекламная платформа', {
            'fields': ('html_code',),
            'description': 'HTML/JS-код платформы (AdSense, Яндекс.Директ и т.п.).',
        }),
        ('Ссылка', {
            'fields': ('url',),
            'description': 'Куда ведёт клик. Обязательно для текста и баннера.',
        }),
        ('Расписание', {
            'fields': ('start_date', 'end_date'),
        }),
        ('Статистика', {
            'fields': ('impressions', 'clicks'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('impressions', 'clicks')




@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


# ============================================================
#  НАСТРОЙКИ САЙТА (РЕЖИМ ОБСЛУЖИВАНИЯ)
# ============================================================
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    # Запрещаем добавлять больше одной записи
    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)




from django.contrib import admin
admin.site.index_template = 'admin/custom_index.html'