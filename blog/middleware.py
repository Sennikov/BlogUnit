from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import SiteSettings

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем админку, статику и загруженные картинки, чтобы они работали
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        try:
            # Берем настройки из БД
            site_settings = SiteSettings.objects.first()

            # Если режим включен
            if site_settings and site_settings.is_maintenance:
                # Если пользователь авторизован и является админом (персоналом) — пускаем его
                if request.user.is_authenticated and request.user.is_staff:
                    return self.get_response(request)

                # Иначе показываем страницу 503 (Сервис недоступен)
                html = render_to_string('blog/503.html', {
                    'message': site_settings.maintenance_message
                })
                return HttpResponse(html, status=503)

        except Exception:
            # Если БД еще не готова (например, при первом запуске), просто пропускаем
            pass

        return self.get_response(request)