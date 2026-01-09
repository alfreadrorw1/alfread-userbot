"""
Plugins package for Alfread UserBot
"""
import importlib
import pkgutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    'mongodb',
    'connect',
    'ping',
    'utils'
]

def discover_plugins():
    """Discover and import all plugins"""
    plugins = []
    package_dir = Path(__file__).parent
    
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        if module_name != "__init__" and module_name in __all__:
            try:
                module = importlib.import_module(f".{module_name}", __package__)
                plugins.append(module)
                logger.info(f"✅ Loaded plugin: {module_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load plugin {module_name}: {e}")
    
    return plugins