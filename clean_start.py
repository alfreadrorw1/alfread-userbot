#!/usr/bin/env python3
"""
Script untuk clean start bot (stop semua instance)
"""

import os
import sys
import time
import signal
import subprocess

def kill_existing_instances():
    """Kill semua instance bot yang berjalan"""
    
    print("🔄 Stopping all bot instances...")
    
    # Kill dengan pkill
    try:
        subprocess.run(["pkill", "-f", "alfread.py"], 
                      stderr=subprocess.DEVNULL,
                      stdout=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass
    
    # Kill dengan killall python
    try:
        subprocess.run(["killall", "python3"], 
                      stderr=subprocess.DEVNULL,
                      stdout=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass
    
    # Hapus lock files
    lock_files = ['alfread.lock', 'alfread_bot.session', 'alfread_bot.session-journal']
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print(f"🗑️  Deleted: {lock_file}")
    
    # Hapus session files
    for file in os.listdir('.'):
        if file.endswith('.session'):
            try:
                os.remove(file)
                print(f"🗑️  Deleted: {file}")
            except:
                pass
    
    print("✅ Cleanup completed!")
    print("\n🎯 Now run: python alfread.py")

if __name__ == "__main__":
    print("🧹 Alfread UserBot Clean Start")
    print("=" * 40)
    
    kill_existing_instances()
    
    # Tunggu 5 detik
    print("\n⏳ Waiting 5 seconds...")
    time.sleep(5)
    
    # Start bot baru
    print("\n🚀 Starting new bot instance...")
    os.system("python alfread.py")