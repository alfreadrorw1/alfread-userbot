"""
Plugin System untuk Alfread UserBot
Auto-load semua plugin dari folder plugins dengan double-load prevention
"""

import importlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Track loaded plugins untuk mencegah double loading
_loaded_plugins = set()
_registered_plugins = {}

async def load_plugins(client):
    """Load semua plugin dari folder plugins"""
    plugins_dir = Path(__file__).parent
    
    logger.info(f"📂 Loading plugins from: {plugins_dir}")
    
    # Cek apakah directory ada
    if not plugins_dir.exists():
        logger.error(f"❌ Plugin directory tidak ditemukan: {plugins_dir}")
        return []
    
    loaded_plugins = []
    
    try:
        # Dapatkan semua file Python di folder plugins (kecuali __init__.py)
        for item in sorted(plugins_dir.iterdir()):
            if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
                module_name = item.stem
                
                # Skip jika sudah di-load
                if module_name in _loaded_plugins:
                    logger.warning(f"⚠️ Plugin {module_name} sudah di-load sebelumnya, skipping...")
                    continue
                
                try:
                    logger.info(f"🔄 Loading plugin: {module_name}")
                    
                    # Unload module jika sudah ada (precaution)
                    if module_name in sys.modules:
                        logger.debug(f"Unloading existing module: {module_name}")
                        del sys.modules[f"plugins.{module_name}"]
                    
                    # Import module
                    module = importlib.import_module(f".{module_name}", package="plugins")
                    
                    # Jika module memiliki fungsi 'register_plugin'
                    if hasattr(module, 'register_plugin'):
                        try:
                            # Register plugin dan track
                            await module.register_plugin(client)
                            _loaded_plugins.add(module_name)
                            _registered_plugins[module_name] = client
                            loaded_plugins.append(module_name)
                            logger.info(f"✅ Plugin loaded: {module_name}")
                        except Exception as e:
                            logger.error(f"❌ Error registering plugin {module_name}: {e}")
                    else:
                        logger.warning(f"⚠️ Module {module_name} tidak memiliki register_plugin function")
                        
                except ImportError as e:
                    logger.error(f"❌ Import error for plugin {module_name}: {e}")
                except Exception as e:
                    logger.error(f"❌ Unexpected error loading plugin {module_name}: {e}")
        
        if loaded_plugins:
            logger.info(f"📦 Total {len(loaded_plugins)} plugin loaded: {', '.join(sorted(loaded_plugins))}")
        else:
            logger.warning("⚠️ No plugins were loaded successfully!")
            
        return loaded_plugins
        
    except Exception as e:
        logger.error(f"❌ Error loading plugins: {e}")
        return []

def unload_plugin(plugin_name):
    """Unload plugin tertentu"""
    if plugin_name in _loaded_plugins:
        _loaded_plugins.remove(plugin_name)
        logger.info(f"✅ Plugin {plugin_name} unloaded")
        return True
    return False