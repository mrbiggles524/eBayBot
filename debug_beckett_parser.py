"""
Comprehensive debug script for Beckett parser
This will show exactly what's on the page and why cards aren't being found
"""
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.beckett.com/news/2025-26-topps-chrome-basketball-cards/"

import sys
import io
# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("BECKETT PARSER DEBUG SCRIPT")
print("=" * 80)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("\n1. FETCHING PAGE...")
import time
response = None
for attempt in range(5):
    try:
        print(f"   Attempt {attempt + 1}/5...")
        response = requests.get(url, headers=headers, timeout=120)
        if response.status_code == 200:
            print(f"   OK: Success! Status: {response.status_code}")
            print(f"   OK: Content length: {len(response.content)} bytes")
            break
        elif response.status_code == 504:
            print(f"   WARNING: Gateway timeout (504), retrying...")
            if attempt < 4:
                time.sleep(5)
                continue
            else:
                print(f"   ERROR: Still getting 504 after 5 attempts")
                print(f"   ERROR: Beckett.com server is timing out")
                exit(1)
        else:
            response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"   WARNING: Request timeout, retrying...")
        if attempt < 4:
            time.sleep(5)
            continue
        else:
            print(f"   ERROR: Still timing out after 5 attempts")
            exit(1)
    except Exception as e:
        print(f"   ERROR: {e}")
        if attempt < 4:
            time.sleep(3)
            continue
        else:
            exit(1)

if not response:
    print("   ERROR: Could not fetch page")
    exit(1)

print("\n2. PARSING HTML...")
soup = BeautifulSoup(response.content, 'html.parser')
all_text = soup.get_text()
print(f"   ✓ Extracted text length: {len(all_text)} characters")
print(f"   ✓ First 200 chars: {repr(all_text[:200])}")

print("\n3. SEARCHING FOR CARD PATTERNS...")

# Look for "1 Pascal Siakam"
pascal_idx = all_text.find('1 Pascal Siakam')
if pascal_idx != -1:
    print(f"   ✓ Found '1 Pascal Siakam' at position {pascal_idx}")
    print(f"   ✓ Context (500 chars):")
    print(f"   {repr(all_text[pascal_idx:pascal_idx+500])}")
else:
    print(f"   ✗ '1 Pascal Siakam' NOT FOUND")

# Look for "1 " followed by capital
one_match = re.search(r'\b1\s+[A-Z]', all_text)
if one_match:
    print(f"   ✓ Found '1 [A-Z]' pattern at position {one_match.start()}")
    print(f"   ✓ Match: {one_match.group(0)}")
    print(f"   ✓ Context (300 chars):")
    print(f"   {repr(all_text[one_match.start():one_match.start()+300])}")
else:
    print(f"   ✗ '1 [A-Z]' pattern NOT FOUND")

print("\n4. TESTING REGEX PATTERNS...")

# Pattern 1: Line-by-line match (what the working version uses)
print("\n   Pattern 1: Line-by-line match (^\\d+\\s+[A-Za-z\\s\\'\\-]+,\\s*[A-Za-z\\s\\'\\-]+)")
lines = all_text.split('\n')
line_matches = []
for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        continue
    match = re.match(r'^(\d+)\s+([A-Za-z\s\'\-\u00C0-\u017F]+),\s*([A-Za-z\s\'\-\u00C0-\u017F]+?)(?:\s+RC)?$', line)
    if match:
        card_num, player_name, team = match.groups()
        line_matches.append((i, line, card_num, player_name.strip(), team.strip()))
        if len(line_matches) <= 5:
            print(f"      Line {i}: {line[:80]}")

print(f"   ✓ Found {len(line_matches)} line-by-line matches")
if line_matches:
    print(f"   ✓ First match: {line_matches[0][1][:100]}")
    print(f"   ✓ Last match: {line_matches[-1][1][:100]}")

# Pattern 2: Multiline regex
print("\n   Pattern 2: Multiline regex (\\d{1,3}\\s+[A-Z][^,\\n]+?,\\s*[A-Z][A-Za-z\\s]+)")
pattern2 = re.compile(r'(\d{1,3})\s+([A-Z][^,\n]+?),\s*([A-Z][A-Za-z\s]+)', re.MULTILINE)
multiline_matches = list(pattern2.finditer(all_text))
print(f"   ✓ Found {len(multiline_matches)} multiline matches")
if multiline_matches:
    print(f"   ✓ First match: {multiline_matches[0].group(0)[:100]}")
    print(f"   ✓ Last match: {multiline_matches[-1].group(0)[:100]}")

# Pattern 3: Very simple
print("\n   Pattern 3: Very simple (\\d{1,3}\\s+[A-Z][^,\\n]+?,\\s*[A-Z][^0-9\\n]+)")
pattern3 = re.compile(r'(\d{1,3})\s+([A-Z][^,\n]+?),\s*([A-Z][^0-9\n]+)', re.MULTILINE)
simple_matches = list(pattern3.finditer(all_text))
print(f"   ✓ Found {len(simple_matches)} simple matches")
if simple_matches:
    print(f"   ✓ First match: {simple_matches[0].group(0)[:100]}")

print("\n5. ANALYZING TEXT STRUCTURE...")

# Find where cards might be
card_sections = []
for keyword in ['Base Set', 'base set', '1 Pascal', '1 ', 'Pascal Siakam']:
    idx = all_text.find(keyword)
    if idx != -1:
        card_sections.append((keyword, idx, all_text[idx:idx+200]))
        print(f"   ✓ Found '{keyword}' at position {idx}")
        print(f"     Context: {repr(all_text[idx:idx+200])}")

# Look for "Parallels" to find where base set ends
parallels_idx = all_text.find('Parallels')
if parallels_idx != -1:
    print(f"   ✓ Found 'Parallels' at position {parallels_idx}")
    print(f"   ✓ Text before Parallels (last 500 chars):")
    print(f"     {repr(all_text[max(0, parallels_idx-500):parallels_idx])}")

print("\n6. SAMPLE OF ACTUAL TEXT (first 2000 chars)...")
print("=" * 80)
print(all_text[:2000])
print("=" * 80)

print("\n7. SUMMARY...")
print(f"   Total text length: {len(all_text)}")
print(f"   Line-by-line matches: {len(line_matches)}")
print(f"   Multiline matches: {len(multiline_matches)}")
print(f"   Simple matches: {len(simple_matches)}")

if len(line_matches) > 0:
    print(f"\n   ✓ SUCCESS: Line-by-line pattern found {len(line_matches)} cards!")
    print(f"   ✓ This pattern should work in the parser")
elif len(multiline_matches) > 0:
    print(f"\n   ⚠ WARNING: Line-by-line failed, but multiline found {len(multiline_matches)} cards")
    print(f"   ⚠ Parser might need to use multiline pattern")
elif len(simple_matches) > 0:
    print(f"\n   ⚠ WARNING: Line-by-line and multiline failed, but simple found {len(simple_matches)} cards")
    print(f"   ⚠ Parser might need to use simple pattern")
else:
    print(f"\n   ✗ ERROR: NO PATTERNS FOUND ANY CARDS!")
    print(f"   ✗ The page structure might be different than expected")

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
