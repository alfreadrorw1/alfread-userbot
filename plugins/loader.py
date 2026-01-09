import importlib
import os
from telethon import events

async def load_plugins_for_client(client, user_id):
    """Load semua plugin untuk client tertentu"""
    from plugins import discover_plugins
    
    loaded_plugins = []
    
    for plugin_name in discover_plugins():
        try:
            # Import plugin module
            module = importlib.import_module(f"plugins.{plugin_name}")
            
            # Cek jika plugin memiliki fungsi setup
            if hasattr(module, 'setup'):
                await module.setup(client, user_id)
                loaded_plugins.append(plugin_name)
                
            # Atau jika plugin memiliki fungsi untuk menambahkan handler
            elif hasattr(module, 'add_handler_to_client'):
                await module.add_handler_to_client(client, user_id)
                loaded_plugins.append(plugin_name)
                
            # Atau jika plugin adalah handler biasa
            elif hasattr(module, 'handler'):
                client.add_event_handler(module.handler, events.NewMessage())
                loaded_plugins.append(plugin_name)
                
        except Exception as e:
            print(f"❌ Error loading plugin {plugin_name} for user {user_id}: {e}")
    
    print(f"✅ Loaded {len(loaded_plugins)} plugins for user {user_id}: {', '.join(loaded_plugins)}")
    return loaded_plugins

async def load_specific_plugin(plugin_name, client, user_id):
    """Load plugin tertentu"""
    try:
        module = importlib.import_module(f"plugins.{plugin_name}")
        
        if hasattr(module, 'setup'):
            await module.setup(client, user_id)
        elif hasattr(module, 'add_handler_to_client'):
            await module.add_handler_to_client(client, user_id)
        elif hasattr(module, 'handler'):
            client.add_event_handler(module.handler, events.NewMessage())
        
        print(f"✅ Loaded plugin: {plugin_name} for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error loading plugin {plugin_name}: {e}")
        return False