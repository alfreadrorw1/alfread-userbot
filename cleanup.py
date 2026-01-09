#!/usr/bin/env python3
import os
import time
import sqlite3

def cleanup_locks():
    """Bersihkan semua lock file dan database"""
    print("🧹 Cleaning up lock files...")
    
    # Hapus file session
    cache_files = [
        'cache/bot.session',
        'cache/user.session',
        'cache/bot.session-journal',
        'cache/user.session-journal',
        'cache/bot',
        'cache/user',
        'data/sessions.json',
    ]
    
    for file in cache_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Removed: {file}")
            except:
                print(f"⚠️ Cannot remove: {file}")
    
    # Hapus semua file di cache dengan pattern
    if os.path.exists('cache'):
        for fname in os.listdir('cache'):
            if fname.startswith('bot_') or fname.startswith('user_'):
                try:
                    os.remove(os.path.join('cache', fname))
                    print(f"✅ Removed: cache/{fname}")
                except:
                    pass
    
    # Hapus pycache
    pycache_dirs = ['__pycache__', 'plugins/__pycache__']
    for dir in pycache_dirs:
        if os.path.exists(dir):
            try:
                import shutil
                shutil.rmtree(dir)
                print(f"✅ Removed: {dir}")
            except:
                print(f"⚠️ Cannot remove: {dir}")
    
    print("\n✅ Cleanup complete!")

if __name__ == '__main__':
    cleanup_locks()