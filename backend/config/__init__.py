"""
SafeRoute AI Configuration Package
Micro Project 14: AI-Based Road Accident Prediction
Integrated COs: CO1, CO2, CO3, CO4, CO5
"""
import os
import sys

# On Windows, register torch/lib DLL directory early before C-runtime initialization
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
    try:
        import torch
    except Exception:
        pass
