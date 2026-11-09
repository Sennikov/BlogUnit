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

    return "git" # Крайний случай, если ничего не нашли

def get_git_info():
    cached_info = cache.get('git_info')
    if cached_info:
        return cached_info

    info = {'version': 'unknown', 'update_available': False, 'error': None, 'branch': 'unknown'}
    git = get_git_executable() # Получаем правильный путь к git

    try:
        version = subprocess.check_output([git, 'describe', '--tags', '--always'], cwd=settings.BASE_DIR, stderr=subprocess.STDOUT).decode('utf-8').strip()
        info['version'] = version

        branch = subprocess.check_output([git, 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=settings.BASE_DIR, stderr=subprocess.STDOUT).decode('utf-8').strip()
        info['branch'] = branch

        subprocess.run([git, 'fetch'], cwd=settings.BASE_DIR, check=True, capture_output=True)

        local_hash = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=settings.BASE_DIR).decode().strip()
        remote_hash = subprocess.check_output([git, 'rev-parse', f'origin/main'], cwd=settings.BASE_DIR).decode().strip()

        info['update_available'] = (local_hash != remote_hash)
    except Exception as e:
        info['error'] = str(e)

    cache.set('git_info', info, 300)
    return info

def apply_git_update():
    cache.delete('git_info')
    logs = []
    git = get_git_executable() # Используем правильный путь

    try:
        pull_result = subprocess.run([git, 'pull', 'origin', 'main'], cwd=settings.BASE_DIR, capture_output=True, text=True, check=True)
        logs.append(f"✅ Git Pull:\n{pull_result.stdout}")

        migrate_result = subprocess.run([sys.executable, 'manage.py', 'migrate'], cwd=settings.BASE_DIR, capture_output=True, text=True, check=True)
        logs.append(f"✅ Миграции:\n{migrate_result.stdout}")

        static_result = subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], cwd=settings.BASE_DIR, capture_output=True, text=True, check=True)
        logs.append(f"✅ Статика:\n{static_result.stdout}")

        if os.name == 'nt':  # Windows
            logs.append("ℹ️ Локальная среда (Windows): пропущен перезапуск Gunicorn.")
        else:
            restart_result = subprocess.run(['sudo', 'systemctl', 'restart', 'gunicorn'], capture_output=True, text=True, check=True)
            logs.append("✅ Служба Gunicorn перезапущена.")
    except Exception as e:
        logs.append(f"❌ ОШИБКА: {str(e)}")
    return "\n".join(logs)