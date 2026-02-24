"""Update eBay token in .env file."""
import os
import re

# The token you provided
token_string = "v^1.1#i^1#r^0#f^0#I^3#p^3#t^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"

env_file = ".env"

# Read existing .env
env_content = ""
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()

# Update or add EBAY_PRODUCTION_TOKEN
if "EBAY_PRODUCTION_TOKEN=" in env_content:
    env_content = re.sub(r'EBAY_PRODUCTION_TOKEN=.*', f'EBAY_PRODUCTION_TOKEN={token_string}', env_content, flags=re.MULTILINE)
else:
    env_content += f"\nEBAY_PRODUCTION_TOKEN={token_string}\n"

# Set USE_OAUTH to false
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

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("Token updated in .env file!")
print("   - EBAY_PRODUCTION_TOKEN set")
print("   - USE_OAUTH set to false")
print("   - EBAY_ENVIRONMENT set to production")
print()
print("Now restart the app and policies should load!")
