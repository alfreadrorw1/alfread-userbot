import importlib
import pkgutil
from pathlib import Path

__all__ = []
__plugins__ = []

def load_plugins():
    plugins_dir = Path(__file__).parent
    for module_info in pkgutil.iter_modules([str(plugins_dir)]):
        if module_info.name not in ["__init__"]:
            module = importlib.import_module(f"plugins.{module_info.name}")
            __plugins__.append(module)
            __all__.append(module_info.name)

load_plugins()