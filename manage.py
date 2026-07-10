#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        tiene_puerto_explicito = any(not arg.startswith('-') for arg in sys.argv[2:])
        if not tiene_puerto_explicito:
            from pathlib import Path
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).resolve().parent / '.env')
            sys.argv.insert(2, os.environ.get('PORT', '8000'))

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
