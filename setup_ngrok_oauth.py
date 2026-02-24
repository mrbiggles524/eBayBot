"""
Setup script to use ngrok for OAuth redirect (HTTPS requirement).
This creates an HTTPS tunnel to localhost for eBay OAuth.
"""
import subprocess
import requests
import time
import json
from config import Config

def get_ngrok_url():
    """Get the current ngrok tunnel URL."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
    except:
        pass
    return None

def start_ngrok(port=8080):
    """Start ngrok tunnel."""
    print("=" * 80)
    print("Setting up ngrok for OAuth (HTTPS redirect)")
    print("=" * 80)
    print()
    print("[WARNING] You need ngrok installed!")
    print("   Download from: https://ngrok.com/download")
    print("   Or install via: choco install ngrok (if you have Chocolatey)")
    print()
    
    # Check if ngrok is running
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"[OK] ngrok is already running: {ngrok_url}")
        return ngrok_url
    
    print("Starting ngrok...")
    print(f"   This will create an HTTPS tunnel to localhost:{port}")
    print()
    
    try:
        # Start ngrok
        process = subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Get the URL
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            print(f"[OK] ngrok started successfully!")
            print(f"   HTTPS URL: {ngrok_url}")
            print()
            print("[WARNING] Keep this terminal open while using OAuth!")
            print("   Press Ctrl+C to stop ngrok when done.")
            print()
            return ngrok_url
        else:
            print("[ERROR] Could not get ngrok URL. Is ngrok installed?")
            return None
            
    except FileNotFoundError:
        print("[ERROR] ngrok not found!")
        print()
        print("Please install ngrok:")
        print("1. Download from: https://ngrok.com/download")
        print("2. Extract and add to PATH")
        print("3. Or use: choco install ngrok")
        return None
    except Exception as e:
        print(f"[ERROR] Error starting ngrok: {e}")
        return None

def update_redirect_uri(ngrok_url):
    """Update .env with ngrok redirect URI."""
    callback_url = f"{ngrok_url}/callback"
    
    print("=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print()
    print(f"1. Go to: https://developer.ebay.com/my/keys")
    print(f"2. Click 'User Tokens' for your Sandbox app")
    print(f"3. Edit your OAuth redirect URL entry")
    print(f"4. Set 'Your auth accepted URL1' to:")
    print(f"   {callback_url}")
    print(f"5. Make sure 'OAuth Enabled' is checked")
    print(f"6. Save")
    print()
    print("Then run: python get_oauth_token.py")
    print()
    
    # Update .env
    try:
        with open(".env", "r") as f:
            content = f.read()
        
        # Update or add OAUTH_REDIRECT_URI
        if "OAUTH_REDIRECT_URI=" in content:
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if line.startswith("OAUTH_REDIRECT_URI="):
                    new_lines.append(f"OAUTH_REDIRECT_URI={callback_url}")
                else:
                    new_lines.append(line)
            content = "\n".join(new_lines)
        else:
            content += f"\nOAUTH_REDIRECT_URI={callback_url}\n"
        
        with open(".env", "w") as f:
            f.write(content)
        
        print(f"[OK] Updated .env with redirect URI: {callback_url}")
        
    except Exception as e:
        print(f"[WARNING] Could not update .env automatically: {e}")
        print(f"   Please manually set: OAUTH_REDIRECT_URI={callback_url}")

if __name__ == "__main__":
    ngrok_url = start_ngrok()
    if ngrok_url:
        update_redirect_uri(ngrok_url)
    else:
        print("\n[ERROR] Failed to set up ngrok. Please install it first.")
