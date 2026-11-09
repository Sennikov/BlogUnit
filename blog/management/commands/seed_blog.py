"""
Наполнение сайта тестовыми категориями и статьями.

Использование:
    python manage.py seed_blog                  # создать (уже существующее пропустит)
    python manage.py seed_blog --reset          # удалить всё и создать заново
    python manage.py seed_blog --posts 15       # 15 статей на категорию
    python manage.py seed_blog --reset --posts 5
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from unidecode import unidecode

from blog.models import Category, Post


# (название, родитель, menu_order, show_in_header, show_in_sidebar)
CATEGORIES = [
    ('Новости',      None,          10, True,  True),
    ('Технологии',   None,          20, True,  True),
    ('Честный знак', None,          50, True,  True),
    ('ИТ',           'Технологии',  10, True,  True),
    ('Игры',         'Технологии',  20, True,  True),
    ('ПО',           'Технологии',  30, True,  True),
]

# Заголовки по категориям (листовым)
TITLES = {
    'Новости': [
        'Что нового в мире технологий за неделю',
        'Крупнейшие IT-компании объявили о партнёрстве',
        'Российский рынок ПО показал рост на 20%',
        'Открытие нового технопарка в Москве',
        'Государство выделит гранты на разработку ИИ',
        'Итоги года: главные события индустрии',
    ],
    'ИТ': [
        'Введение в Django 5: что нового',
        '10 полезных библиотек Python в 2026 году',
        'Как выбрать между FastAPI и Django',
        'PostgreSQL vs MySQL: что выбрать в 2026',
        'Docker для начинающих: первые шаги',
        'Git: 15 команд, которые надо знать',
        'Паттерны проектирования на Python',
        'Асинхронность в Python: полный гайд',
        'Тестирование Django-приложений',
        'Кэширование в Django: Redis и Memcached',
        'Микросервисы vs монолит: что выбрать',
        'CI/CD с GitHub Actions за 30 минут',
    ],
    'Игры': [
        'Обзор Cyberpunk 2077 после всех патчей',
        'Топ-10 инди-игр 2026 года',
        'Как создают игры: интервью с разработчиком',
        'God of War Ragnarök: полный разбор',
        'Инди-разработчик заработал миллион за месяц',
        'Почему игры на Python — плохая идея',
        'Обзор новой игровой консоли',
        'Киберспорт в России: итоги сезона',
        'Ретро-игры, которые стоит пройти',
        'Секреты оптимизации игрового движка',
    ],
    'ПО': [
        'Обзор новых версий офисных пакетов',
        'Open Source vs проприетарное ПО',
        'Как выбрать CRM для малого бизнеса',
        'Бесплатные аналоги Photoshop',
        'Антивирусы 2026: что выбрать',
        'Linux для дома: с чего начать',
        'Менеджеры паролей: обзор решений',
        'Программы для монтажа видео',
        'Бухгалтерия в облаке: обзор сервисов',
        'Лучшие IDE для Python в 2026',
    ],
    'Честный знак': [
        'Что такое Честный знак и зачем он нужен',
        'Маркировка обуви: инструкция для продавцов',
        'Штрафы за продажу немаркированных товаров',
        'Как зарегистрироваться в Честном знаке',
        'Маркировка молочной продукции: новшества',
        'Приёмка товаров с маркировкой на складе',
        'Интеграция Честного знака с 1С',
        'Маркировка лекарств: что нужно знать',
        'Табак и алкоголь: особенности маркировки',
        'Что будет с бизнесом после введения маркировки',
        'Ответственность за подделку маркировки',
        'Обзор приложения «Честный знак»',
    ],
}

GENERIC_TITLES = [
    'Обзор за неделю',
    'Главное за месяц',
    'Мнение эксперта',
    'Практический гайд',
    'Новое исследование',
    'Интересные факты',
    'Что почитать на выходных',
    'Коротко о главном',
]

PARAGRAPHS = [
    'Это тестовая статья, созданная для проверки работы блога. '
    'Её можно смело удалить или отредактировать через админку.',
    'В современном мире технологии развиваются с невероятной скоростью. '
    'То, что вчера казалось фантастикой, сегодня становится повседневностью.',
    'Эксперты сходятся во мнении, что главные изменения ещё впереди. '
    'Отрасль ждёт несколько прорывов в ближайшие годы.',
    'Практика показывает: чем раньше начать разбираться в теме, '
    'тем больше преимуществ получишь в долгосрочной перспективе.',
    'Не стоит забывать и о рисках. Любая новая технология — это '
    'не только возможности, но и новые вызовы для бизнеса и общества.',
    'Читателям рекомендуется изучить вопрос самостоятельно и '
    'не полагаться слепо на чужие выводы — контекст всегда важен.',
    'В заключение хочется сказать: следите за обновлениями, '
    'мы будем рассказывать о самом важном по мере появления новостей.',
]


class Command(BaseCommand):
    help = 'Наполняет сайт тестовыми категориями и статьями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить все посты и категории перед созданием',
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=8,
            help='Сколько статей на каждую листовую категорию (по умолчанию 8)',
        )

    def handle(self, *args, **options):
        posts_per_cat = options['posts']

        if options['reset']:
            self.stdout.write(self.style.WARNING('Удаляем все посты и категории...'))
            Post.objects.all().delete()
            Category.objects.all().delete()

        # 1. Создаём категории (корневые сначала)
        self.stdout.write('Создаём категории...')
        created_cats = {}
        for name, parent_name, order, in_header, in_sidebar in CATEGORIES:
            parent = created_cats.get(parent_name) if parent_name else None
            slug = slugify(unidecode(name))
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'parent': parent,
                    'menu_order': order,
                    'show_in_header': in_header,
                    'show_in_sidebar': in_sidebar,
                    'description': f'Тестовая категория «{name}».',
                },
            )
            created_cats[name] = cat
            status = 'создана' if created else 'уже есть'
            self.stdout.write(f'  {name} ({status})')

        # 2. Статьи — только в листовые категории
        self.stdout.write(f'Создаём статьи ({posts_per_cat} на категорию)...')
        total_created = 0

        for cat_name, cat in created_cats.items():
            if cat_name == 'Технологии':
                continue   # у неё есть дети, статьи пусть идут в них

            titles = TITLES.get(cat_name, GENERIC_TITLES)

            for i in range(posts_per_cat):
                base_title = titles[i % len(titles)]
                if i >= len(titles):
                    title = f'{base_title} — часть {i // len(titles) + 1}'
                else:
                    title = base_title

                # slug с проверкой уникальности
                base_slug = slugify(unidecode(title)) or 'post'
                slug = base_slug
                counter = 1
                while Post.objects.filter(slug=slug).exists():
                    slug = f'{base_slug}-{counter}'
                    counter += 1

                # контент из случайных абзацев
                num_paras = random.randint(3, 5)
                content = '\n\n'.join(random.sample(PARAGRAPHS, num_paras))

                # дата публикации в пределах 60 дней
                days_ago = random.randint(0, 60)
                published = timezone.now() - timedelta(days=days_ago)

                Post.objects.create(
                    title=title,
                    slug=slug,
                    content=content,
                    category=cat,
                    published_date=published,
                    is_published=True,
                )
                total_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Категорий: {len(created_cats)}, создано статей: {total_created}.'
        ))
        self.stdout.write('Проверьте сайт: http://127.0.0.1:8000/')