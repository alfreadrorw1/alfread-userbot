"""
Plugin System untuk Alfread UserBot
Auto-load semua plugin dari folder plugins
"""

import importlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Track loaded plugins untuk mencegah double loading
_loaded_plugins = set()

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
        for item in plugins_dir.iterdir():
            if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
                module_name = item.stem
                
                # Skip jika sudah di-load
                if module_name in _loaded_plugins:
                    logger.debug(f"⚠️ Plugin {module_name} sudah di-load, skipping...")
                    continue
                
                try:
                    logger.info(f"🔄 Loading plugin: {module_name}")
                    
                    # Import module
                    module = importlib.import_module(f".{module_name}", package="plugins")
                    
                    # Jika module memiliki fungsi 'register_plugin'
                    if hasattr(module, 'register_plugin'):
                        try:
                            await module.register_plugin(client)
                            _loaded_plugins.add(module_name)
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
            logger.info(f"📦 Total {len(loaded_plugins)} plugin loaded: {', '.join(loaded_plugins)}")
        else:
            logger.warning("⚠️ No plugins were loaded successfully!")
            
        return loaded_plugins
        
    except Exception as e:
        logger.error(f"❌ Error loading plugins: {e}")
        return []