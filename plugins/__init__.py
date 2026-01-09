"""
Plugin System untuk Alfread UserBot dengan double-load protection
"""

import importlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Global tracking untuk mencegah double loading
_loaded_modules = {}  # {client_id: {module_name: True}}
_client_plugins = {}  # {client_id: [plugin_list]}

def get_client_id(client):
    """Dapatkan unique ID untuk client"""
    try:
        return client.session_id
    except AttributeError:
        return id(client)

async def load_plugins(client):
    """Load semua plugin dari folder plugins"""
    
    client_id = get_client_id(client)
    
    # Cek jika client sudah memiliki plugins
    if client_id in _client_plugins:
        logger.warning(f"⚠️ Client {client_id} sudah memiliki plugins, skipping...")
        return _client_plugins[client_id]
    
    plugins_dir = Path(__file__).parent
    
    logger.info(f"📂 Loading plugins for client {client_id} from: {plugins_dir}")
    
    # Cek apakah directory ada
    if not plugins_dir.exists():
        logger.error(f"❌ Plugin directory tidak ditemukan: {plugins_dir}")
        return []
    
    loaded_plugins = []
    
    try:
        # Initialize tracking untuk client ini
        _loaded_modules[client_id] = {}
        
        # Dapatkan semua file Python di folder plugins
        plugin_files = sorted([f for f in plugins_dir.iterdir() 
                              if f.is_file() and f.suffix == '.py' and f.name != '__init__.py'])
        
        logger.info(f"Found {len(plugin_files)} plugin files")
        
        for item in plugin_files:
            module_name = item.stem
            
            # Skip jika sudah di-load untuk client ini
            if _loaded_modules[client_id].get(module_name):
                logger.debug(f"⚠️ Plugin {module_name} already loaded for client {client_id}")
                continue
            
            try:
                logger.info(f"🔄 Loading plugin: {module_name}")
                
                # Import module dengan fresh import
                spec = importlib.util.spec_from_file_location(module_name, item)
                if spec is None:
                    logger.error(f"❌ Cannot find spec for {module_name}")
                    continue
                
                module = importlib.util.module_from_spec(spec)
                
                # Clear module dari sys.modules jika sudah ada
                full_module_name = f"plugins.{module_name}"
                if full_module_name in sys.modules:
                    logger.debug(f"Clearing existing module: {full_module_name}")
                    del sys.modules[full_module_name]
                
                sys.modules[full_module_name] = module
                spec.loader.exec_module(module)
                
                # Jika module memiliki fungsi 'register_plugin'
                if hasattr(module, 'register_plugin'):
                    try:
                        # Cek jika module sudah ter-register di client
                        if hasattr(client, 'registered_plugins'):
                            if module_name in client.registered_plugins:
                                logger.warning(f"⚠️ Module {module_name} already registered in client")
                                continue
                        else:
                            client.registered_plugins = set()
                        
                        await module.register_plugin(client)
                        
                        # Track successful loading
                        _loaded_modules[client_id][module_name] = True
                        client.registered_plugins.add(module_name)
                        loaded_plugins.append(module_name)
                        
                        logger.info(f"✅ Plugin loaded: {module_name}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error registering plugin {module_name}: {e}")
                else:
                    logger.warning(f"⚠️ Module {module_name} tidak memiliki register_plugin function")
                    
            except Exception as e:
                logger.error(f"❌ Error loading plugin {module_name}: {e}")
        
        # Simpan loaded plugins untuk client
        _client_plugins[client_id] = loaded_plugins
        
        if loaded_plugins:
            logger.info(f"📦 Total {len(loaded_plugins)} plugins loaded for client {client_id}")
        else:
            logger.warning("⚠️ No plugins were loaded successfully!")
            
        return loaded_plugins
        
    except Exception as e:
        logger.error(f"❌ Error loading plugins: {e}")
        return []