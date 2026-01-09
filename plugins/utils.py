import json
from datetime import datetime
from plugins.connect import sessions_collection

async def get_prefix_from_mongo(user_id):
    """Ambil prefix dari MongoDB - DIPINDAHKAN dari prefix.py"""
    try:
        if sessions_collection:
            session_data = sessions_collection.find_one({"user_id": str(user_id)})
            
            if session_data and "prefix" in session_data:
                return session_data["prefix"]
            else:
                # Default prefix
                default_prefix = "."
                await save_prefix_to_mongo(user_id, default_prefix)
                return default_prefix
        
        return "."
    except Exception as e:
        print(f"❌ Error getting prefix from MongoDB: {e}")
        return "."

async def save_prefix_to_mongo(user_id, prefix):
    """Simpan prefix ke MongoDB"""
    try:
        if sessions_collection:
            result = sessions_collection.update_one(
                {"user_id": str(user_id)},
                {
                    "$set": {
                        "prefix": prefix,
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
            return result.acknowledged
        return False
    except Exception as e:
        print(f"❌ Error saving prefix to MongoDB: {e}")
        return False

def format_time(seconds):
    """Format waktu menjadi string yang mudah dibaca"""
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds or not parts: parts.append(f"{seconds}s")
    
    return ' '.join(parts)

# Export functions
__all__ = [
    'get_prefix_from_mongo',
    'save_prefix_to_mongo',
    'format_time'
]