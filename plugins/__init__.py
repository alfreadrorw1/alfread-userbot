"""
Plugin System untuk Alfread UserBot
Auto-load semua plugin dari folder plugins
"""

import importlib
import pkgutil
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

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
                
                try:
                    # Import module
                    spec = importlib.util.spec_from_file_location(
                        f"plugins.{module_name}", 
                        str(item)
                    )
                    
                    if spec is None:
                        logger.warning(f"⚠️ Cannot load spec for: {module_name}")
                        continue
                    
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"plugins.{module_name}"] = module
                    spec.loader.exec_module(module)
                    
                    # Jika module memiliki fungsi 'register_plugin'
                    if hasattr(module, 'register_plugin'):
                        try:
                            await module.register_plugin(client)
                            loaded_plugins.append(module_name)
                            logger.info(f"✅ Plugin loaded: {module_name}")
                        except Exception as e:
                            logger.error(f"❌ Error registering plugin {module_name}: {e}")
                    else:
                        logger.warning(f"⚠️ Module {module_name} tidak memiliki register_plugin function")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to load plugin {module_name}: {e}")
        
        logger.info(f"📦 Total {len(loaded_plugins)} plugin loaded: {', '.join(loaded_plugins)}")
        return loaded_plugins
        
    except Exception as e:
        logger.error(f"❌ Error loading plugins: {e}")
        return []