"""Fix token configuration - switch from OAuth to User Token mode."""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Your User Token
USER_TOKEN = "v^1.1#i^1#r^0#f^0#p^3#I^3#t^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"

env_file = ".env"

print("=" * 70)
print("Fixing Token Configuration")
print("=" * 70)
print()

# Read .env
if not os.path.exists(env_file):
    print(f"ERROR: {env_file} not found!")
    sys.exit(1)

with open(env_file, 'r', encoding='utf-8') as f:
    env_content = f.read()

# Update EBAY_PRODUCTION_TOKEN
if "EBAY_PRODUCTION_TOKEN=" in env_content:
    env_content = re.sub(r'EBAY_PRODUCTION_TOKEN=.*', f'EBAY_PRODUCTION_TOKEN={USER_TOKEN}', env_content, flags=re.MULTILINE)
else:
    env_content += f"\nEBAY_PRODUCTION_TOKEN={USER_TOKEN}\n"

# Set USE_OAUTH to false (User Token mode)
if "USE_OAUTH=" in env_content:
    env_content = re.sub(r'USE_OAUTH=.*', 'USE_OAUTH=false', env_content, flags=re.MULTILINE)
else:
    env_content += "USE_OAUTH=false\n"

# Ensure EBAY_ENVIRONMENT is production
if "EBAY_ENVIRONMENT=" in env_content:
    env_content = re.sub(r'EBAY_ENVIRONMENT=.*', 'EBAY_ENVIRONMENT=production', env_content, flags=re.MULTILINE)
else:
    env_content += "EBAY_ENVIRONMENT=production\n"

# Write back
with open(env_file, 'w', encoding='utf-8') as f:
    f.write(env_content)

# Clear old OAuth token file
oauth_file = ".ebay_token.json"
if os.path.exists(oauth_file):
    os.remove(oauth_file)
    print(f"Removed old OAuth token file: {oauth_file}")

print()
print("Token configuration fixed!")
print("  - USE_OAUTH set to false (User Token mode)")
print("  - EBAY_PRODUCTION_TOKEN updated")
print("  - EBAY_ENVIRONMENT set to production")
print("  - Old OAuth token file removed")
print()
print("Now restart the app (stop and start python app.py)")
