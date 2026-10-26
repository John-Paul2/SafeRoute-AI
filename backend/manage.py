#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.
SafeRoute AI Project - Micro Project 14
Integrated COs: CO1, CO2, CO3, CO4, CO5
"""
import os
import sys

# On Windows, add torch/lib directory so DLLs (c10.dll, etc.) initialize properly
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    try:
        import site
        search_dirs = list(site.getsitepackages()) if hasattr(site, "getsitepackages") else []
        search_dirs.extend(sys.path)
        for sp in search_dirs:
            t_lib = os.path.join(sp, "torch", "lib")
            if os.path.isdir(t_lib):
                os.add_dll_directory(t_lib)
                break
    except Exception:
        pass

# Pre-load torch on Windows before any C-runtime or graphics DLL is initialized
try:
    import torch
except Exception:
    pass

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
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
