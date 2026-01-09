#!/usr/bin/env python3
"""
Cek apakah ada multiple instances bot yang berjalan
"""

import os
import sys
import subprocess

def check_bot_instances():
    """Cek process bot yang sedang berjalan"""
    try:
        # Cari process python yang menjalankan alfread
        cmd = "ps aux | grep alfread.py | grep -v grep"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        lines = result.stdout.strip().split('\n')
        if not lines[0]:
            print("✅ Tidak ada instance bot yang berjalan")
            return 0
        
        print(f"⚠️ Ditemukan {len(lines)} instance bot:")
        for i, line in enumerate(lines, 1):
            print(f"{i}. {line[:100]}")
        
        return len(lines)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return -1

if __name__ == "__main__":
    count = check_bot_instances()
    if count > 1:
        print("\n🚨 **SOLUSI:** Kill semua instance dulu:")
        print("1. pkill -f alfread.py")
        print("2. Tunggu 10 detik")
        print("3. python alfread.py")
    sys.exit(0)