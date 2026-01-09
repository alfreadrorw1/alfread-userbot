import importlib
import os
import asyncio
from telethon import events

async def load_plugins_for_client(client, user_id):
    """
    Fungsi legacy untuk kompatibilitas
    Sekarang menggunakan auto-load system dari __init__.py
    """
    try:
        # Gunakan auto-load system yang baru
        from plugins import auto_load_all_plugins_for_client
        return await auto_load_all_plugins_for_client(client, user_id)
    except Exception as e:
        print(f"❌ Error in legacy load_plugins_for_client: {e}")
        return []

async def load_specific_plugin(plugin_name, client, user_id):
    """
    Load plugin tertentu
    Fungsi legacy untuk kompatibilitas
    """
    try:
        # Gunakan auto-load system yang baru
        from plugins import auto_setup_plugin_for_client
        return await auto_setup_plugin_for_client(client, user_id, plugin_name)
    except Exception as e:
        print(f"❌ Error in legacy load_specific_plugin: {e}")
        return False

# Fungsi untuk register handler secara manual (jika diperlukan)
def register_event_handler(client, handler, event_type=events.NewMessage, **kwargs):
    """Register event handler ke client"""
    try:
        client.add_event_handler(handler, event_type(**kwargs))
        return True
    except Exception as e:
        print(f"❌ Error registering event handler: {e}")
        return False

# Fungsi untuk mendapatkan daftar semua plugin
def get_all_plugins():
    """Get list of all available plugins"""
    plugins = []
    plugins_dir = "plugins"
    
    if not os.path.exists(plugins_dir):
        return plugins
    
    for item in os.listdir(plugins_dir):
        if item.endswith('.py') and item not in ['__init__.py', 'connect.py', 'bot_handler.py', 'loader.py', 'utils.py']:
            plugin_name = item[:-3]  # Remove .py extension
            plugins.append(plugin_name)
    
    return plugins

# Fungsi untuk cek jika plugin valid
def is_valid_plugin(plugin_name):
    """Check if a plugin is valid (has proper setup function)"""
    try:
        module = importlib.import_module(f"plugins.{plugin_name}")
        
        # Cek fungsi setup
        if hasattr(module, 'setup') or hasattr(module, 'add_handler_to_client'):
            return True
        
        # Cek export
        if hasattr(module, '__all__'):
            for func_name in module.__all__:
                if func_name.startswith('add_') and func_name.endswith('_handler_to_client'):
                    return True
        
        return False
    except:
        return False

# Export functions untuk kompatibilitas
__all__ = [
    'load_plugins_for_client',
    'load_specific_plugin',
    'register_event_handler',
    'get_all_plugins',
    'is_valid_plugin'
]