import os
import uuid
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

@csrf_exempt
@staff_member_required
def markdown_uploader(request):
    if request.method == 'POST':
        # Martor передает файл именно под этим именем
        file = request.FILES.get('markdown-image-upload') or request.FILES.get('file')

        if not file:
            return JsonResponse({'status': 400, 'error': 'Файл не передан'}, status=400)

        ext = os.path.splitext(file.name)[1].lower()

        # Генерируем уникальное имя файла
        filename = f"{uuid.uuid4().hex}{ext}"

        # Формируем путь: uploads/2026/10/xxxxxx.jpg
        now = timezone.now()
        path = f"uploads/{now:%Y/%m}/{filename}"

        # Сохраняем файл в MEDIA_ROOT
        saved_path = default_storage.save(path, ContentFile(file.read()))

        # Получаем URL для вставки в Markdown
        file_url = default_storage.url(saved_path)

        # Возвращаем JSON, который ожидает Martor
        return JsonResponse({
            'status': 200,
            'link': file_url,
            'name': file.name
        })

    return JsonResponse({'status': 405, 'error': 'Invalid request'}, status=405)