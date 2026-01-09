#!/usr/bin/env python3
import subprocess
import sys

def install_packages():
    """Install required packages"""
    packages = [
        "telethon==1.34.0",
        "python-telegram-bot==20.7",
        "python-dotenv==1.0.0",
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\n✅ All packages installed successfully!")

if __name__ == "__main__":
    install_packages()