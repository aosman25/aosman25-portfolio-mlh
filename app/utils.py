import hashlib
from urllib.parse import quote_plus

def generate_avatar(email: str, name: str):
    email = email.lower().strip()
    avatar_base_url = "https://gravatar.com/avatar"
    ui_avatar_path = f"/{quote_plus(name)}/128/0D8ABC/FFFFFF/2/0.35/true/true/false/png"
    fallback_url = f"https://ui-avatars.com/api{ui_avatar_path}"
    fallback_url_encoded = quote_plus(fallback_url)  
    hashed_email = hashlib.md5(email.encode('utf-8')).hexdigest()
    return  f"{avatar_base_url}/{hashed_email}?d={fallback_url_encoded}"