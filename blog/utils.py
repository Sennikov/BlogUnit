import subprocess
import sys
import os
import shutil
from django.conf import settings
from django.core.cache import cache

def get_git_executable():
    """Ищет путь к git, чтобы избежать ошибки [WinError 2] на Windows."""
    # 1. Пытаемся найти в системном PATH (работает на Linux и в Git Bash)
    git_path = shutil.which("git")
    if git_path:
        return git_path

    # 2. Если не нашли и это Windows, проверяем стандартные пути установки
    if os.name == 'nt':
        possible_paths = [
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe"
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p

    return "git" # Крайний случай

def get_git_info():
    """Проверяет версию и наличие обновлений (с кэшем на 5 минут)."""
    cached_info = cache.get('git_info')
    if cached_info:
        return cached_info

    info = {'version': 'unknown', 'update_available': False, 'error': None, 'branch': 'unknown'}
    git = get_git_executable()

    try:
        # Получаем версию (тег или хэш)
        version = subprocess.check_output([git, 'describe', '--tags', '--always'], cwd=settings.BASE_DIR, stderr=subprocess.STDOUT).decode('utf-8').strip()
        info['version'] = version

        # Получаем название ветки
        branch = subprocess.check_output([git, 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=settings.BASE_DIR, stderr=subprocess.STDOUT).decode('utf-8').strip()
        info['branch'] = branch

        # Проверяем обновления на GitHub
        subprocess.run([git, 'fetch'], cwd=settings.BASE_DIR, check=True, capture_output=True)

        local_hash = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=settings.BASE_DIR).decode().strip()
        remote_hash = subprocess.check_output([git, 'rev-parse', 'origin/main'], cwd=settings.BASE_DIR).decode().strip()

        info['update_available'] = (local_hash != remote_hash)
    except Exception as e:
        info['error'] = str(e)

    # Кэшируем результат на 5 минут (300 секунд)
    cache.set('git_info', info, 300)
    return info

def apply_git_update():
    """Выполняет git pull, миграции, сбор статики и перезапуск Gunicorn."""
    # Очищаем кэш, чтобы после обновления статус пересчитался заново
    cache.delete('git_info')
    logs = []
    git = get_git_executable()

    try:
        # 1. Git Pull
        pull_result = subprocess.run([git, 'pull', 'origin', 'main'], cwd=settings.BASE_DIR, capture_output=True, text=True, check=True)
        logs.append(f"✅ Git Pull:\n{pull_result.stdout}")

        # 2. Миграции
        migrate_result = subprocess.run([sys.executable, 'manage.py', 'migrate'], cwd=settings.BASE_DIR, capture_output=True, text=True, check=True)
        logs.append(f"✅ Миграции:\n{migrate_result.stdout}")

        # 3. Сбор статики
        static_result = subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], cwd=settings.BASE_DIR, capture_output=True, text=True, check=True)
        logs.append(f"✅ Статика:\n{static_result.stdout}")

        # 4. Перезапуск Gunicorn (безопасный для самого скрипта)
        if os.name == 'nt':  # Windows
            logs.append("ℹ️ Локальная среда (Windows): пропущен перезапуск Gunicorn.")
        else:
            # Выполняем перезапуск, НЕ вызывая ошибку, если процесс убит (SIGTERM)
            restart_result = subprocess.run(['sudo', 'systemctl', 'restart', 'gunicorn'])

            # Код 0 - успех, код -15 (или 143) - успешное убийство процесса при перезапуске
            if restart_result.returncode in (0, -15, 143):
                logs.append("✅ Служба Gunicorn успешно перезапущена.")
            else:
                logs.append(f"⚠️ Gunicorn перезапущен с кодом {restart_result.returncode}.")

    except Exception as e:
        logs.append(f"❌ ОШИБКА: {str(e)}")

    return "\n".join(logs)