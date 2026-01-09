#!/usr/bin/env python3
"""
Script untuk generate session string untuk Railway deployment
Jalankan di lokal, lalu copy session string ke Railway environment variables
"""

import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import Config

async def generate_session():
    """Generate session string untuk Railway"""
    print("🔧 Generating session string for Railway...")
    
    client = TelegramClient(
        StringSession(),
        Config.API_ID,
        Config.API_HASH
    )
    
    await client.start()
    
    # Dapatkan session string
    session_string = client.session.save()
    
    print("\n✅ Session String berhasil digenerate!")
    print("=" * 50)
    print(session_string)
    print("=" * 50)
    
    print("\n📋 Copy string di atas dan tambahkan ke Railway Environment Variables:")
    print("1. Buka project di Railway")
    print("2. Pergi ke tab 'Variables'")
    print("3. Tambahkan variable baru:")
    print("   Key: SESSION_STRING")
    print(f"   Value: {session_string}")
    print("\n4. Redeploy aplikasi")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_session())