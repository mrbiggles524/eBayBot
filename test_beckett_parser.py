"""Test script to debug Beckett parser."""
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.beckett.com/news/2025-bowman-draft-baseball-cards/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("Fetching URL...")
response = requests.get(url, headers=headers, timeout=60)
print(f"Status: {response.status_code}")

soup = BeautifulSoup(response.content, 'html.parser')

# Look for Base Set section
print("\n=== Looking for Base Set heading ===")
for heading in soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong', 'b']):
    text = heading.get_text().strip()
    if 'base' in text.lower() and 'set' in text.lower():
        print(f"Found heading: {text}")
        print(f"Tag: {heading.name}")
        print(f"Next sibling: {heading.next_sibling}")

# Look for card patterns in the HTML
print("\n=== Looking for card patterns in text ===")
all_text = soup.get_text()
lines = all_text.split('\n')

card_count = 0
for i, line in enumerate(lines[:500]):  # Check first 500 lines
    line = line.strip()
    if re.match(r'^BD-\d+', line) or re.match(r'^BDC-\d+', line):
        print(f"Line {i}: {line[:100]}")
        card_count += 1
        if card_count >= 10:  # Show first 10 matches
            break

# Look for specific HTML elements that might contain cards
print("\n=== Looking for list items ===")
for li in soup.find_all('li')[:20]:
    text = li.get_text().strip()
    if re.match(r'^BD-\d+', text) or re.match(r'^BDC-\d+', text):
        print(f"Found in <li>: {text[:80]}")

print("\n=== Looking for paragraphs ===")
for p in soup.find_all('p')[:30]:
    text = p.get_text().strip()
    if re.match(r'^BD-\d+', text) or re.match(r'^BDC-\d+', text):
        print(f"Found in <p>: {text[:80]}")

print("\n=== Sample of raw text (first 2000 chars) ===")
print(all_text[:2000])
