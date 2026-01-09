"""
Plugin System untuk Alfread UserBot
Auto-load semua plugin dari folder plugins
"""

import importlib
import pkgutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def load_plugins(client):
    """Load semua plugin dari folder plugins"""
    plugins_dir = Path(__file__).parent
    loaded_plugins = []
    
    # Cari semua file .py di folder plugins
    for module_info in pkgutil.iter_modules([str(plugins_dir)]):
        # Skip __init__ dan file yang diawali underscore
        if module_info.name.startswith('_'):
            continue
        
        # Skip file yang bukan .py
        if not module_info.ispkg and not module_info.name.endswith('.py'):
            continue
            
        try:
            # Import module
            module = importlib.import_module(f"plugins.{module_info.name.replace('.py', '')}")
            
            # Jika module memiliki fungsi 'register_plugin'
            if hasattr(module, 'register_plugin'):
                try:
                    await module.register_plugin(client)
                    loaded_plugins.append(module_info.name)
                    logger.info(f"✅ Plugin loaded: {module_info.name}")
                except Exception as e:
                    logger.error(f"❌ Error registering plugin {module_info.name}: {e}")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import plugin {module_info.name}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error loading plugin {module_info.name}: {e}")
    
    logger.info(f"📦 Total {len(loaded_plugins)} plugin loaded: {', '.join(loaded_plugins)}")
    return loaded_plugins