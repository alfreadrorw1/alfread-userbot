import importlib
import pkgutil
import sys

# Dictionary untuk menyimpan plugin handlers
PLUGIN_HANDLERS = {}

def register_plugin(name, handler_function):
    """Register plugin handler"""
    PLUGIN_HANDLERS[name] = handler_function

def get_plugin_handler(name):
    """Get plugin handler by name"""
    return PLUGIN_HANDLERS.get(name)

def discover_plugins():
    """Discover semua plugin di folder plugins"""
    plugins = []
    
    # Import semua module di folder plugins
    for _, module_name, is_pkg in pkgutil.iter_modules(['plugins']):
        if module_name not in ['__init__', 'connect', 'bot_handler']:
            plugins.append(module_name)
    
    return plugins

# Auto import semua plugin saat module di-load
__all__ = discover_plugins()