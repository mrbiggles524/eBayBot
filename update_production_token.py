"""
Update .env file with Production token.
"""
import os
from pathlib import Path

def update_env_token(token: str):
    """Update .env file with production token."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("[ERROR] .env file not found!")
        return False
    
    # Read current .env
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update token and OAuth setting
    updated_lines = []
    token_updated = False
    oauth_updated = False
    
    for line in lines:
        if line.strip().startswith('EBAY_PRODUCTION_TOKEN='):
            updated_lines.append(f'EBAY_PRODUCTION_TOKEN={token}\n')
            token_updated = True
        elif line.strip().startswith('USE_OAUTH='):
            updated_lines.append('USE_OAUTH=false\n')
            oauth_updated = True
        else:
            updated_lines.append(line)
    
    # If token wasn't found, add it
    if not token_updated:
        updated_lines.append(f'\n# Production Token\nEBAY_PRODUCTION_TOKEN={token}\n')
    
    # If OAuth setting wasn't found, add it
    if not oauth_updated:
        updated_lines.append('USE_OAUTH=false\n')
    
    # Write back
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    print("=" * 80)
    print("[OK] Updated .env file with Production token")
    print("=" * 80)
    print()
    print("Changes made:")
    print(f"  - EBAY_PRODUCTION_TOKEN={token[:50]}...")
    print("  - USE_OAUTH=false")
    print()
    print("Next steps:")
    print("  1. Test: python check_keyset_status.py")
    print("  2. Create production drafts: python -m streamlit run start.py")
    print()
    
    return True

if __name__ == "__main__":
    token = "v^1.1#i^1#I^3#p^3#r^1#f^0#t^Ul4xMF8zOjExQzM1Q0Q1NzUzMDIxODRDQUEwMUJEMjAxREVBQjA3XzJfMSNFXjI2MA=="
    update_env_token(token)
