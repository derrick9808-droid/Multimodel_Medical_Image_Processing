#!/usr/bin/env python
"""Django manage.py for MedAI platform."""
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medai_platform.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Could not import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
