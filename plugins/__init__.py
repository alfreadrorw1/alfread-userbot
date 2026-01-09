import importlib
import pkgutil
import sys
import asyncio
from telethon import TelegramClient

# Dictionary untuk menyimpan plugin handlers
PLUGIN_HANDLERS = {}
PLUGIN_SETUP_FUNCTIONS = {}

def register_plugin(name, handler_function):
    """Register plugin handler"""
    PLUGIN_HANDLERS[name] = handler_function

def get_plugin_handler(name):
    """Get plugin handler by name"""
    return PLUGIN_HANDLERS.get(name)

async def auto_setup_plugin_for_client(client, user_id, plugin_name):
    """Auto setup plugin untuk client tertentu"""
    try:
        # Coba import module
        spec = importlib.util.find_spec(f"plugins.{plugin_name}")
        if spec is None:
            print(f"⚠️ Plugin {plugin_name} not found")
            return False
            
        module = importlib.import_module(f"plugins.{plugin_name}")
        
        # Cek dan panggil fungsi setup yang sesuai
        if hasattr(module, 'add_handler_to_client'):
            success = await module.add_handler_to_client(client, user_id)
            if success:
                print(f"✅ Auto-loaded {plugin_name} for user {user_id}")
                return True
        elif hasattr(module, 'setup'):
            success = await module.setup(client, user_id)
            if success:
                print(f"✅ Auto-loaded {plugin_name} for user {user_id}")
                return True
        
        # Cek jika ada fungsi handler langsung
        elif hasattr(module, 'handler'):
            client.add_event_handler(module.handler)
            print(f"✅ Auto-loaded {plugin_name} for user {user_id}")
            return True
        
        print(f"⚠️ Plugin {plugin_name} has no setup function")
        return False
    except Exception as e:
        print(f"❌ Error auto-loading plugin {plugin_name}: {e}")
        return False

async def auto_load_all_plugins_for_client(client, user_id):
    """Auto load semua plugin untuk client tertentu"""
    print(f"🚀 Auto-loading plugins for user {user_id}...")
    
    loaded_plugins = []
    failed_plugins = []
    
    # Import semua plugin dari folder plugins
    for _, module_name, is_pkg in pkgutil.iter_modules(['plugins']):
        # Skip module sistem
        if module_name in ['__init__', 'connect', 'bot_handler', 'loader', 'utils']:
            continue
            
        try:
            success = await auto_setup_plugin_for_client(client, user_id, module_name)
            if success:
                loaded_plugins.append(module_name)
            else:
                failed_plugins.append(module_name)
        except Exception as e:
            print(f"❌ Failed to auto-load {module_name}: {e}")
            failed_plugins.append(module_name)
    
    print(f"✅ Auto-loaded {len(loaded_plugins)} plugins")
    if failed_plugins:
        print(f"⚠️ Failed to load: {', '.join(failed_plugins)}")
    
    return loaded_plugins

def discover_plugins():
    """Discover semua plugin di folder plugins"""
    plugins = []
    
    try:
        # Import semua module di folder plugins
        for _, module_name, is_pkg in pkgutil.iter_modules(['plugins']):
            # Skip module sistem
            if module_name not in ['__init__', 'connect', 'bot_handler', 'loader', 'utils']:
                plugins.append(module_name)
    except Exception as e:
        print(f"❌ Error discovering plugins: {e}")
    
    return plugins

# Export fungsi untuk auto-load
__all__ = [
    'auto_load_all_plugins_for_client',
    'auto_setup_plugin_for_client',
    'register_plugin',
    'get_plugin_handler'
]