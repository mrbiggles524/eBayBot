"""
Switch to production environment and configure for draft-only listings.
"""
import os
from pathlib import Path

def switch_to_production():
    """Switch .env file to production environment."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("[ERROR] .env file not found!")
        print("Please create a .env file first with your credentials.")
        return False
    
    # Read current .env
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update EBAY_ENVIRONMENT
    updated_lines = []
    environment_updated = False
    
    for line in lines:
        if line.strip().startswith('EBAY_ENVIRONMENT='):
            updated_lines.append('EBAY_ENVIRONMENT=production\n')
            environment_updated = True
        else:
            updated_lines.append(line)
    
    # If EBAY_ENVIRONMENT wasn't found, add it
    if not environment_updated:
        updated_lines.append('\n# eBay Environment\n')
        updated_lines.append('EBAY_ENVIRONMENT=production\n')
    
    # Write back
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 80)
    print("[OK] Switched to PRODUCTION Environment")
    print("=" * 80)
    print()
    print("⚠️  IMPORTANT:")
    print("   - All API calls will now go to PRODUCTION eBay")
    print("   - Listings will be created as DRAFTS (not published)")
    print("   - You can view them in your eBay Seller Hub")
    print("   - Make sure your production OAuth token is set up")
    print()
    print("Next steps:")
    print("   1. Verify your production credentials are in .env")
    print("   2. Run: python -m streamlit run start.py")
    print("   3. Create listings - they will be saved as drafts")
    print()
    
    return True

if __name__ == "__main__":
    switch_to_production()
