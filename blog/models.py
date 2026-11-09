from itertools import chain

from django.db import models
import os
import uuid
from django.utils.text import slugify
from unidecode import unidecode
from martor.models import MartorField
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError


#Модель Создания/Редоктирования категорий на сайте.

class Category(models.Model):
    name = models.CharField(verbose_name='Название категории', max_length=200, unique=True)
    description = models.TextField(verbose_name='Описание категории', blank=True)
    slug = models.SlugField(verbose_name='URL - категории', max_length=200, unique=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,blank=True,
        related_name= 'children',
        verbose_name = 'Родительская категория',
        help_text = 'Оставьте пустым, если это категория верхнего уровня.',
    )

    show_in_header = models.BooleanField(default=False, verbose_name='Показывать в ТОП - Меню')
    show_in_sidebar = models.BooleanField(default=False, verbose_name= 'Показывать в сайдбаре')
    show_in_footer = models.BooleanField(default=False, verbose_name='Показывать Подвал - Меню')
    footer_order = models.PositiveIntegerField(default=0, verbose_name='Порядок в Меню - подвала')
    menu_order = models.PositiveBigIntegerField(default=0, verbose_name='Порядок в меню')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['menu_order', 'name']

    def get_absolute_url(self):
        return reverse('blog:slug_detail', kwargs={'slug': self.slug})

    def get_ancestors(self):
        chain = []
        current = self
        while current is not None:
            chain.append(current)
            current = current.parent
        return list(reversed(chain))

    def descendants_ids(self):
        ids = [self.pk]
        stack = list(self.children.all())
        while stack:
            cat = stack.pop()
            ids.append(cat.pk)
            stack.extend(cat.children.all())
        return ids

    def clean(self):
        current = self.parent
        while current is not None:
            if current.pk == self.pk:
                # from django.core.exceptions import ValidationError
                raise ValidationError({'parent': 'Категория не может быть потомком свмой себя. '})
            current = current.parent

    def __str__(self):
        return self.name

#Модель Создания/Редоктирования статей на сайте.

#Создание превью для статьи раскладывается по дате загрузки.

def preview_upload_path(instance, filename):
    """Путь: media/posts/previews/YYYY/MM/<имя файла>"""
    ext = os.path.splitext(filename)[1].lower()
    now = timezone.now()
    return f'posts/previews/{now:%Y/%m}/{filename}'


# ============================================================
#  ТЕГИ
# ============================================================
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название тега')
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_published=True,
            published_date__lte=timezone.now()
        )


class Post(models.Model):
    title = models.CharField(verbose_name= 'Заголовок статьи', max_length=200)
    slug = models.SlugField(verbose_name='URL статьи (автозаполнение)', max_length=200, unique=True, blank=True,)

    preview = models.ImageField(verbose_name='Загрузите превью для статьи',upload_to=preview_upload_path,blank=True,null=True)
    content = MartorField('Текст статьи')

    seo_title = models.CharField(
        verbose_name='SEO заголовок (Title)',
        max_length=255,
        blank=True,
        help_text='Заголовок для поисковиков и вкладки браузера. Если пусто — возьмется обычный заголовок статьи.'
    )


    meta_description = models.TextField(
        verbose_name= 'Meta описание (анонс)',
        max_length = 255,
        blank = True,
        help_text = 'Краткое описание для поисковиков и соцсетей (до 160 символов). Если пусто — возьмется текст статьи.'
    )

    menu_title = models.CharField(max_length=100, blank=True, verbose_name='Название в меню')
    show_in_header = models.BooleanField(default=False, verbose_name='Показывать в шапке')
    show_in_sidebar = models.BooleanField(default=False, verbose_name='Показывать в сайдбаре')
    show_in_footer = models.BooleanField(default=False, verbose_name='Показывать в Меню - Подвал')
    footer_order = models.PositiveIntegerField(default=0, verbose_name='Порядок в Меню - Подвал')
    menu_order = models.PositiveIntegerField(default=0, verbose_name='Порядок в меню')

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank= True,
        related_name = 'posts',
        verbose_name = 'Категория',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts',
        verbose_name='Теги'
    )

    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False,verbose_name='Опубликовано')
    views = models.PositiveBigIntegerField(default=0, verbose_name='Просмотры')

    objects = models.Manager()
    published = PublishedManager()

    def get_absolute_url(self):
        if self.category_id:
            return reverse('blog:post_detail', kwargs={
                'category_slug': self.category.slug,
                'post_slug': self.slug,
            })
        return reverse('blog:slug_detail', kwargs={'slug': self.slug}) # ← поменяли на slug_detail

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(unidecode(self.title)) or 'post'
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug

        if self.is_published and not self.published_date:
            self.published_date=timezone.now()

        super().save(*args, **kwargs)

    def menu_label(self):
        """Название пункта меню: menu_title, если задан, иначе title."""
        return self.menu_title or self.title

    def publish(self):
        self.is_published = True
        if not self.published_date:
            self.published_date = timezone.now()
        self.save()

    def unpublish(self):
        """Метод, чтобы снять публикацию"""
        self.is_published = False
        self.save()

    def __str__(self):
        return self.title

class PageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category__isnull=True, is_published=True)

class Page(Post):
    objects = PageManager()  # ✅ ТЕПЕРЬ ИСПОЛЬЗУЕТСЯ ВАШ МЕНЕДЖЕР
    published = PublishedManager()
    class Meta:
        proxy = True
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'
        ordering = ['title']


# ============================================================
#  ПРОКСИ-МОДЕЛЬ ЧЕРНОВИКОВ (неопубликованные посты без категории)
# ============================================================

class DraftManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(category__isnull=True, is_published=False)
        )


class Draft(Post):
    objects = DraftManager()

    class Meta:
        proxy = True
        verbose_name = 'Черновик'
        verbose_name_plural = 'Черновики'
        ordering = ['-created_date']



# ============================================================
#  РЕКЛАМНЫЕ БЛОКИ
# ============================================================
def ad_image_upload_path(instance, filename):
    """media/ads/YYYY/MM/<uuid>.ext"""
    ext = os.path.splitext(filename)[1].lower() or '.jpg'
    now = timezone.now()
    return f'ads/{now:%Y/%m}/{uuid.uuid4().hex}{ext}'


class AdBlock(models.Model):
    TYPE_TEXT = 'text'
    TYPE_IMAGE = 'image'
    TYPE_PLATFORM = 'platform'
    TYPE_CHOICES = [
        (TYPE_TEXT, 'Текстовая реклама'),
        (TYPE_IMAGE, 'Баннер (картинка)'),
        (TYPE_PLATFORM, 'Рекламная платформа (HTML/JS)'),
    ]

    POSITION_SIDEBAR = 'sidebar'
    POSITION_HEADER = 'header'
    POSITION_BETWEEN_POSTS = 'between_posts'
    POSITION_CHOICES = [
        (POSITION_SIDEBAR, 'Сайдбар'),
        (POSITION_HEADER, 'Под шапкой'),
        (POSITION_BETWEEN_POSTS, 'Между статьями в ленте'),
    ]

    title = models.CharField(
        verbose_name='Название (для админки)', max_length=200,
        help_text='Внутреннее имя, чтобы отличать блоки друг от друга.',
    )
    position = models.CharField(
        verbose_name='Позиция', max_length=20,
        choices=POSITION_CHOICES, default=POSITION_SIDEBAR,
    )
    type = models.CharField(
        verbose_name='Тип блока', max_length=20,
        choices=TYPE_CHOICES, default=TYPE_TEXT,
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    text = models.TextField(
        verbose_name='Текст рекламы', blank=True,
        help_text='Для типа «Текстовая реклама».',
    )
    image = models.ImageField(
        verbose_name='Баннер', upload_to=ad_image_upload_path,
        blank=True, null=True,
        help_text='Для типа «Баннер». 240×200, 300×250, 300×600 и т.п.',
    )
    image_alt = models.CharField(
        verbose_name='Alt-текст баннера', max_length=200, blank=True,
    )
    url = models.URLField(
        verbose_name='Ссылка', blank=True,
        help_text='Куда ведёт клик. Для текста и баннера.',
    )
    html_code = models.TextField(
        verbose_name='HTML/JS-код', blank=True,
        help_text='Для типа «Рекламная платформа». Вставится как есть.',
    )

    start_date = models.DateTimeField(
        verbose_name='Начать показ', null=True, blank=True,
        help_text='Оставьте пустым, чтобы показывать сразу.',
    )
    end_date = models.DateTimeField(
        verbose_name='Закончить показ', null=True, blank=True,
        help_text='Оставьте пустым, чтобы показывать бессрочно.',
    )

    impressions = models.PositiveIntegerField(default=0, verbose_name='Показы', editable=False)
    clicks = models.PositiveIntegerField(default=0, verbose_name='Клики', editable=False)

    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Рекламный блок'
        verbose_name_plural = 'Реклама'
        ordering = ['position', 'order', 'title']
        indexes = [
            models.Index(fields=['position', 'is_active', 'order']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.type == self.TYPE_TEXT and not self.text.strip():
            raise ValidationError({'text': 'Для текстовой рекламы заполните текст.'})
        if self.type == self.TYPE_IMAGE:
            if not self.image:
                raise ValidationError({'image': 'Для баннера загрузите изображение.'})
            if not self.url:
                raise ValidationError({'url': 'Для баннера укажите ссылку.'})
        if self.type == self.TYPE_PLATFORM and not self.html_code.strip():
            raise ValidationError({'html_code': 'Для платформы вставьте HTML/JS-код.'})

        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'Дата окончания должна быть позже даты начала.'})

    @property
    def is_visible(self):
        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def get_click_url(self):
        if self.url:
            return f'/ads/click/{self.pk}/'
        return ''

    def __str__(self):
        return f'[{self.get_position_display()}] {self.title} ({self.get_type_display()})'



# ============================================================
#  НАСТРОЙКИ САЙТА (РЕЖИМ ОБСЛУЖИВАНИЯ)
# ============================================================
class SiteSettings(models.Model):
    is_maintenance = models.BooleanField(
        default=False,
        verbose_name="Режим обслуживания (закрыть сайт)"
    )
    maintenance_message = models.TextField(
        default="Мы проводим технические работы. Скоро вернемся!",
        verbose_name="Сообщение для посетителей"
    )

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return "Настройки сайта"










