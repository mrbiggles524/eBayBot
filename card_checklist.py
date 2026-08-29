"""Card checklist fetcher from various sources."""
import requests
import csv
import os
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from config import Config

class CardChecklistFetcher:
    """Fetches card checklists from various sources."""
    
    def __init__(self, source: Optional[str] = None):
        self.config = Config()
        self.source = source or self.config.CARD_DATA_SOURCE
    
    def get_set_checklist(self, set_name: str = None, csv_file: str = None) -> List[Dict]:
        """
        Get checklist for a card set.
        
        Args:
            set_name: Name of the card set (if not using CSV)
            csv_file: Path to CSV file with card data
            
        Returns:
            List of card dictionaries with name, number, and other info
        """
        if csv_file:
            return self._fetch_from_csv(csv_file)
        elif self.source == 'tcgplayer':
            return self._fetch_from_tcgplayer(set_name)
        elif self.source == 'scryfall':
            return self._fetch_from_scryfall(set_name)
        elif self.source == 'beckett':
            return self._fetch_from_beckett(set_name)
        else:
            return self._fetch_custom(set_name)
    
    def _fetch_from_tcgplayer(self, set_name: str) -> List[Dict]:
        """Fetch checklist from TCGPlayer API."""
        if not self.config.TCGPLAYER_API_KEY:
            raise ValueError("TCGPlayer API key not configured")
        
        # TCGPlayer API endpoint for set search
        url = "https://api.tcgplayer.com/catalog/products"
        headers = {
            "Authorization": f"Bearer {self._get_tcgplayer_token()}",
            "Accept": "application/json"
        }
        
        params = {
            "categoryId": 1,  # Trading Cards category
            "productName": set_name,
            "limit": 100
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            cards = []
            for product in data.get('results', []):
                cards.append({
                    'name': product.get('name', ''),
                    'number': product.get('number', ''),
                    'rarity': product.get('rarity', ''),
                    'set_name': set_name,
                    'product_id': product.get('productId', ''),
                    'image_url': product.get('imageUrl', '')
                })
            
            return cards
        except Exception as e:
            print(f"Error fetching from TCGPlayer: {e}")
            return []
    
    def _get_tcgplayer_token(self) -> str:
        """Get TCGPlayer API access token."""
        url = "https://api.tcgplayer.com/token"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.TCGPLAYER_API_KEY,
            "client_secret": ""  # TCGPlayer uses client_id as secret for some endpoints
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('access_token', '')
    
    def _fetch_from_scryfall(self, set_name: str) -> List[Dict]:
        """Fetch checklist from Scryfall API (for Magic: The Gathering)."""
        # Scryfall API endpoint
        url = f"https://api.scryfall.com/cards/search"
        params = {
            "q": f'set:"{set_name}"',
            "order": "set",
            "unique": "prints"
        }
        
        try:
            cards = []
            has_more = True
            
            while has_more:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for card in data.get('data', []):
                    cards.append({
                        'name': card.get('name', ''),
                        'number': card.get('collector_number', ''),
                        'rarity': card.get('rarity', ''),
                        'set_name': card.get('set_name', set_name),
                        'set_code': card.get('set', ''),
                        'image_url': card.get('image_uris', {}).get('normal', ''),
                        'mana_cost': card.get('mana_cost', ''),
                        'type_line': card.get('type_line', '')
                    })
                
                has_more = data.get('has_more', False)
                if has_more:
                    url = data.get('next_page', '')
                    params = {}
            
            return sorted(cards, key=lambda x: int(x['number']) if x['number'].isdigit() else 999)
        except Exception as e:
            print(f"Error fetching from Scryfall: {e}")
            return []
    
    def _fetch_from_csv(self, csv_file: str) -> List[Dict]:
        """Fetch checklist from CSV file."""
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        cards = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    # Normalize column names (case-insensitive, handle spaces)
                    normalized_row = {k.strip().lower().replace(' ', '_'): v for k, v in row.items()}
                    
                    card = {
                        'name': normalized_row.get('name') or normalized_row.get('card_name') or '',
                        'number': normalized_row.get('number') or normalized_row.get('card_number') or normalized_row.get('collector_number') or '',
                        'set_name': normalized_row.get('set_name') or normalized_row.get('set') or '',
                        'rarity': normalized_row.get('rarity') or '',
                        'image_url': normalized_row.get('image_url') or normalized_row.get('image') or '',
                        'price': float(normalized_row.get('price', 0)) if normalized_row.get('price') else None,
                        'quantity': int(normalized_row.get('quantity', 1)) if normalized_row.get('quantity') else 1,
                        'condition': normalized_row.get('condition') or '',
                        'weight': float(normalized_row.get('weight', 0.1)) if normalized_row.get('weight') else 0.1
                    }
                    
                    # Add any additional fields
                    for key, value in normalized_row.items():
                        if key not in ['name', 'card_name', 'number', 'card_number', 'collector_number',
                                      'set_name', 'set', 'rarity', 'image_url', 'image', 'price',
                                      'quantity', 'condition', 'weight']:
                            card[key] = value
                    
                    if card['name']:  # Only add if name exists
                        cards.append(card)
            
            print(f"Loaded {len(cards)} cards from CSV file: {csv_file}")
            return cards
            
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            raise
    
    def _fetch_from_beckett(self, set_name_or_url: str) -> List[Dict]:
        """Fetch checklist from Beckett.com - ONLY base set cards with numbers."""
        cards = []
        
        # Check if input is a URL
        if set_name_or_url.startswith('http'):
            url = set_name_or_url
        else:
            print("Please provide the full Beckett checklist URL")
            return []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # Increase timeout for slow connections
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=headers, timeout=60)  # Increased to 60 seconds
                    response.raise_for_status()
                    break
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        print(f"[DEBUG] Timeout on attempt {attempt + 1}, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        raise
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        print(f"[DEBUG] Request error on attempt {attempt + 1}: {e}, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        raise
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the Base Set section specifically
            base_section = None
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                heading_text = heading.get_text().strip().lower()
                if 'base set' in heading_text and 'insert' not in heading_text:
                    base_section = heading
                    break
            
            # Get content area - focus on base set section if found
            if base_section:
                # Get content after the base set heading, up to next major section
                content_area = base_section.find_next_sibling()
                if not content_area:
                    parent = base_section.find_parent()
                    if parent:
                        content_area = parent
            else:
                content_area = soup.find('div', class_=re.compile('content|article|post', re.I))
                if not content_area:
                    content_area = soup.find('article') or soup.find('main') or soup
            
            if not content_area:
                content_area = soup
            
            # Extract text
            text_content = content_area.get_text() if content_area else soup.get_text()
            lines = text_content.split('\n')
            
            seen_cards = set()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                line_lower = line.lower()
                # Skip insert/parallel keywords
                if any(skip in line_lower for skip in [
                    'cards', 'parallel', 'refractor', 'insert', 'autograph', 'signature',
                    'shop for', 'checklist', 'team set', 'parallels', 'superfractor',
                    'geometric', 'aqua', 'blue', 'green', 'purple', 'gold', 'orange',
                    'red', 'white', 'black', '/1', '/2', '/5', '/10', '/25', '/50',
                    '/75', '/99', '/150', '/199', '/275', '/299', '/399', 'raywave',
                    'pulsar', 'magenta', 'teal', 'yellow', 'chromographs', 'signature style',
                    'next stop', 'destiny', 'tall tales', 'go time', 'helix', 'instinct',
                    'generation rising', 'rock stars', 'inspirational', 'advisory',
                    'glass canvas', 'youthquake', 'loading', 'ultra violet', 'activators',
                    'serenity', 'voices', 'xs and whoas', 'radiating rookies', 'finals',
                    'stratospheric', 'topps chrome autographs'
                ]):
                    continue
                
                # Skip if line is just a small number (like "1", "3", "10", "15", "20", "23", "25")
                if line.isdigit() and int(line) < 100:
                    continue
                
                # Flexible pattern to match any card number format:
                # - "BD-1 Player Name, Team"
                # - "BDC-1 Player Name, Team"
                # - "#1 Player Name, Team"
                # - "1 Player Name, Team"
                # - Any prefix-number format followed by name and team
                match = re.match(r'^(?:[A-Z]{0,5}[-#]|#)?(\d+)\s+([A-Za-z\s\'\-\u00C0-\u017F\.]+),\s*([A-Za-z\s\'\-\u00C0-\u017F\.]+?)(?:\s+RC)?$', line)
                if match:
                    card_num, player_name, team = match.groups()
                    card_num = card_num.strip()
                    player_name = player_name.strip()
                    team = team.strip()
                    
                    # Skip if player name looks like an insert code
                    if re.search(r'^[A-Z]{3,}-\d+', player_name):
                        continue
                    if len(player_name) < 2:
                        continue
                    # Skip if team has numbering info
                    if re.search(r'/\d+', team):
                        continue
                    if len(team) < 2 or len(team) > 60:
                        continue
                    
                    # Skip if card number is too high
                    try:
                        num_val = int(card_num)
                        if num_val > 500:
                            continue
                    except:
                        continue
                    
                    card_key = (card_num, player_name.lower())
                    if card_key not in seen_cards:
                        seen_cards.add(card_key)
                        cards.append({
                            'number': card_num,
                            'name': player_name,
                            'team': team,
                            'set_name': set_name_or_url,
                            'type': 'base',
                            'rarity': 'Base'
                        })
            
            # Sort by card number - base cards are just numbers 1-300
            # Sort numerically: 1, 2, 3... not alphabetically
            def sort_key(card):
                num = str(card.get('number', ''))
                if not num:
                    return 999
                # Base cards are just numbers (no prefixes)
                try:
                    if num.isdigit():
                        return int(num)
                    # If it has a prefix, put it at the end (shouldn't happen for base)
                    return 999
                except:
                    return 999
            
            cards.sort(key=sort_key)
            
            print(f"Found {len(cards)} base set cards from Beckett checklist")
            if len(cards) > 0:
                first_10 = [f"{c['number']} {c['name']}" for c in cards[:10]]
                last_5 = [f"{c['number']} {c['name']}" for c in cards[-5:]]
                print(f"First 10 cards: {first_10}")
                print(f"Last 5 cards: {last_5}")
            return cards
            
        except Exception as e:
            print(f"Error fetching from Beckett: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_insert_section(self, element, insert_name: str) -> List[Dict]:
        """Parse an insert card section from Beckett - NOT USED (we only want base cards)."""
        # We don't want insert cards, so return empty
        return []
    
    def extract_description_from_page(self, soup: BeautifulSoup, url: str, checklist_type: str = 'base') -> str:
        """
        Extract description text from the checklist page.
        Looks for paragraphs that describe the product/set.
        
        Args:
            soup: BeautifulSoup object of the page
            url: URL of the page
            checklist_type: Type of checklist ('base', 'inserts', 'parallels', 'autographs', 'numbered')
        
        Returns:
            Description string with HTML formatting
        """
        description_parts = []
        set_name = None
        
        try:
            # Look for the main article or content area
            article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile('content|article|post', re.I))
            if not article:
                article = soup
            
            # Find the set name - try multiple strategies
            # Strategy 1: Look for h1/h2 with card-related keywords
            for heading in article.find_all(['h1', 'h2', 'h3']):
                text = heading.get_text().strip()
                # Look for set name patterns like "2024-25 Topps Chrome Basketball Cards"
                if any(keyword in text.lower() for keyword in ['topps', 'panini', 'bowman', 'cards', 'basketball', 'baseball', 'football', 'draft', 'chrome']):
                    if len(text) > 10 and len(text) < 200:
                        set_name = text
                        print(f"[DESC] Found set name: {set_name}")
                        break
            
            # Strategy 2: If no set name found, try to extract from URL or page title
            if not set_name:
                page_title = soup.find('title')
                if page_title:
                    title_text = page_title.get_text().strip()
                    # Clean up title (remove "Beckett", "Checklist", "Team Sets", etc.)
                    title_text = re.sub(r'\s*[-|]\s*Beckett.*$', '', title_text, flags=re.I)
                    title_text = re.sub(r'\s*Checklist.*$', '', title_text, flags=re.I)
                    title_text = re.sub(r'\s*Team Sets.*$', '', title_text, flags=re.I)
                    title_text = re.sub(r'\s*Box Info.*$', '', title_text, flags=re.I)
                    title_text = re.sub(r'\s*Pre-Order.*$', '', title_text, flags=re.I)
                    title_text = title_text.strip()
                    if len(title_text) > 10 and len(title_text) < 200:
                        set_name = title_text
                        print(f"[DESC] Found set name from page title: {set_name}")
            
            # Strategy 3: Try to extract from URL
            if not set_name:
                # Extract from URL like "2025-26-topps-chrome-basketball-cards"
                url_match = re.search(r'/([^/]+-cards?)/?$', url)
                if url_match:
                    url_text = url_match.group(1).replace('-cards', '').replace('-card', '').replace('-', ' ')
                    # Capitalize properly
                    url_text = ' '.join(word.capitalize() for word in url_text.split())
                    set_name = url_text
                    print(f"[DESC] Found set name from URL: {set_name}")
            
            # Format the heading based on checklist type
            if set_name:
                if checklist_type == 'base':
                    heading_text = f"Base Cards from the {set_name}"
                elif checklist_type == 'inserts':
                    heading_text = f"Insert Cards from the {set_name}"
                elif checklist_type == 'parallels':
                    heading_text = f"Parallel Cards from the {set_name}"
                elif checklist_type == 'autographs':
                    heading_text = f"Autographs from the {set_name}"
                elif checklist_type == 'numbered':
                    heading_text = f"Numbered Cards from the {set_name}"
                else:
                    heading_text = f"Cards from the {set_name}"
                
                description_parts.append(f"<p><strong>{heading_text}</strong></p>")
                print(f"[DESC] Created heading: {heading_text}")
            
            # User wants simple format: "Base Cards from the [set name]" + standard paragraphs only
            # We don't need to extract additional paragraphs - just use the heading we created
            
            # If we found the heading, add standard paragraphs
            # User wants: "Base Cards from the [set name]" + standard paragraphs only
            # Don't include extracted meta descriptions or other paragraphs
            if description_parts and any('<strong>' in p for p in description_parts):
                # Keep only the heading (first part with <strong>)
                heading_only = [p for p in description_parts if '<strong>' in p]
                description_parts = heading_only
                
                # Always add the standard paragraphs
                description_parts.append("<p>Select your card from the dropdown menu.</p>")
                description_parts.append("<p>All cards are in Near Mint or better condition.</p>")
                description_parts.append("<p>Ships in penny sleeve + top loader via PWE with eBay tracking.</p>")
                
                final_desc = '\n'.join(description_parts)
                print(f"[DESC] Final description length: {len(final_desc)} characters")
                return final_desc
            
        except Exception as e:
            print(f"[DEBUG] Error extracting description: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: create a basic description with title if we found one
        # Even if extraction failed, we should return something useful
        if title:
            print(f"[DESC] Using fallback description with title: {title}")
            fallback_desc = f"""<p><strong>{title}</strong></p>
<p>Select your card from the dropdown menu.</p>
<p>All cards are in Near Mint or better condition.</p>
<p>Ships in penny sleeve + top loader via PWE with eBay tracking.</p>"""
            return fallback_desc
        
        # Last resort: minimal description
        print("[DESC] Using minimal fallback description")
        return """<p>Select your card from the dropdown menu.</p>
<p>All cards are in Near Mint or better condition.</p>
<p>Ships in penny sleeve + top loader via PWE with eBay tracking.</p>"""
    
    def fetch_from_beckett_url(self, url: str, checklist_type: str = 'base') -> tuple[List[Dict], str]:
        """
        Fetch checklist directly from a Beckett URL or Cardsmiths Breaks.
        Automatically detects the source and uses the appropriate parser.
        
        Args:
            url: Beckett or Cardsmiths checklist URL
            checklist_type: Type of checklist to fetch
                - 'base': Base set cards only
                - 'inserts': Insert cards only
                - 'parallels': Parallel cards only
                - 'autographs': Autograph cards only
                - 'numbered': Numbered cards only
        
        Returns:
            Tuple of (list of cards, description string)
        """
        # Detect source from URL
        is_cardsmiths = 'cardsmithsbreaks.com' in url.lower()
        is_beckett = 'beckett.com' in url.lower()
        is_cardboard = 'cardboardconnection.com' in url.lower()
        
        # First, fetch the page to extract description
        soup = None
        description = None
        try:
            print(f"[DESC] Fetching page to extract description from: {url}")
            # Prefer cloudscraper via _fetch_page_soup (Beckett often fails plain SSL/requests)
            soup = self._fetch_page_soup(url)
            if soup is None:
                raise RuntimeError('Failed to fetch page for description')
            description = self.extract_description_from_page(soup, url, checklist_type)
            if description:
                print(f"[DESC] Successfully extracted description ({len(description)} chars)")
            else:
                print(f"[DESC] No description extracted, using fallback")
        except Exception as e:
            print(f"[DEBUG] Could not extract description: {e}")
            import traceback
            traceback.print_exc()
            # Even if extraction fails, provide a basic description
            description = """<p>Select your card from the dropdown menu.</p>
<p>All cards are in Near Mint or better condition.</p>
<p>Ships in penny sleeve + top loader via PWE with eBay tracking.</p>"""
            print(f"[DESC] Using fallback description due to extraction error")
        
        if is_cardboard:
            print(f"[PARSER] Detected Cardboard Connection URL - using Cardboard Connection parser")
            cards = self._fetch_base_cards_from_cardboardconnection(url, soup=soup)
            return (cards or [], description)
        
        if is_cardsmiths:
            print(f"[PARSER] Detected Cardsmiths Breaks URL - using Cardsmiths parser")
            if checklist_type == 'base':
                cards = self._fetch_base_cards_from_cardsmiths(url)
                return (cards, description)
            else:
                # For now, only base cards supported from Cardsmiths
                print("Note: Only base cards are supported from Cardsmiths Breaks")
                cards = self._fetch_base_cards_from_cardsmiths(url)
                return (cards, description)
        
        elif is_beckett:
            print(f"[PARSER] Detected Beckett URL - using Beckett parser")
            print(f"[PARSER] Checklist type: {checklist_type}")
            print(f"[PARSER] URL: {url}")
            # Route to appropriate parser based on type - pass soup to avoid re-fetching
            if checklist_type == 'base':
                print(f"[PARSER] ========================================")
                print(f"[PARSER] ROUTING TO BASE CARDS PARSER")
                print(f"[PARSER] checklist_type='{checklist_type}'")
                print(f"[PARSER] URL: {url}")
                print(f"[PARSER] CRITICAL: Must ONLY return base cards 1-300, NO INSERTS")
                print(f"[PARSER] ========================================")
                result = self._fetch_base_cards_from_beckett(url, soup=soup)
                result = self._split_bowman_base_vs_prospects(result, 'base')
                print(f"[PARSER] ========================================")
                print(f"[PARSER] BASE CARDS PARSER RETURNED")
                print(f"[PARSER] Result type: {type(result)}")
                print(f"[PARSER] Result length: {len(result) if result else 0}")
                if result and len(result) > 0:
                    print(f"[PARSER] First card: {result[0]}")
                    if len(result) > 1:
                        print(f"[PARSER] Last card: {result[-1]}")
                    # Prefixed cards may be valid (BP- prospects, BD-/BDC- draft)
                    prefixed = [c for c in result if '-' in str(c.get('number', ''))]
                    if prefixed:
                        print(f"[PARSER] Found {len(prefixed)} prefixed cards in base result (BP-/BD- OK)")
                        for c in prefixed[:5]:
                            print(f"[PARSER]   Prefixed: {c.get('number')} {c.get('name')}")
                print(f"[PARSER] ========================================")
                
                # EMERGENCY SAFEGUARD: Check card count based on format
                if result and len(result) > 0:
                    # Check if this is a prefixed set (BD-/BDC- can have up to 400 cards: 200 BD- + 200 BDC-)
                    has_prefix = any('-' in str(c.get('number', '')) for c in result)
                    if has_prefix:
                        # Prefixed sets: allow up to 410 cards (e.g., Bowman Draft: 200 BD- + 200 BDC- + small buffer for duplicates)
                        max_cards = 410
                        if len(result) > max_cards:
                            print(f"[PARSER] ========================================")
                            print(f"[PARSER] EMERGENCY SAFEGUARD TRIGGERED!")
                            print(f"[PARSER] Got {len(result)} prefixed cards but should be max {max_cards}!")
                            print(f"[PARSER] Rejecting all cards - parser is broken")
                            print(f"[PARSER] ========================================")
                            result = []
                        else:
                            # Always check for duplicates and remove them
                            seen = set()
                            unique_cards = []
                            duplicates = []
                            for card in result:
                                card_key = card.get('number', '')
                                if card_key in seen:
                                    duplicates.append(card_key)
                                else:
                                    seen.add(card_key)
                                    unique_cards.append(card)
                            
                            if duplicates:
                                print(f"[PARSER] Found {len(duplicates)} duplicate cards, removing them...")
                                print(f"[PARSER] Duplicates: {duplicates[:10]}")
                                result = unique_cards
                                print(f"[PARSER] After removing duplicates: {len(result)} unique cards")
                            
                            print(f"[PARSER] Validation passed: {len(result)} prefixed cards (max {max_cards})")
                    else:
                        # Plain-numbered sets: max 300 cards (e.g., Topps Chrome: 1-300)
                        max_cards = 300
                        if len(result) > max_cards:
                            print(f"[PARSER] ========================================")
                            print(f"[PARSER] EMERGENCY SAFEGUARD TRIGGERED!")
                            print(f"[PARSER] Got {len(result)} plain-numbered cards but should be max {max_cards}!")
                            print(f"[PARSER] Rejecting all cards - parser is broken")
                            print(f"[PARSER] ========================================")
                            result = []
                        else:
                            print(f"[PARSER] Validation passed: {len(result)} plain-numbered cards (max {max_cards})")
                
                # VALIDATION: For plain-numbered sets, reject if any have prefixes
                # For prefixed sets (BD-/BDC-), prefixes are expected and valid
                if result:
                    print(f"[PARSER] ========================================")
                    print(f"[PARSER] VALIDATING ALL {len(result)} CARDS...")
                    
                    # Check if this is a prefixed set
                    has_prefix = any('-' in str(c.get('number', '')) for c in result)
                    
                    plain_cards = [c for c in result if str(c.get('number', '')).isdigit()]
                    prefixed_cards = [c for c in result if '-' in str(c.get('number', ''))]
                    mixed_bowman = bool(plain_cards) and bool(prefixed_cards) and all(
                        str(c.get('number', '')).startswith('BP-') for c in prefixed_cards
                    )

                    if mixed_bowman:
                        # Bowman Baseball: veterans 1-N first, then Base Prospects BP-*
                        def _bowman_order(card):
                            n = str(card.get('number', ''))
                            if n.isdigit():
                                return (0, int(n))
                            if n.startswith('BP-'):
                                try:
                                    return (1, int(n.split('-', 1)[1]))
                                except ValueError:
                                    return (1, 9999)
                            return (2, n)

                        result = sorted(result, key=_bowman_order)
                        print(f"[PARSER] Mixed Bowman base detected: {len(plain_cards)} plain + {len(prefixed_cards)} BP-")
                        print(f"[PARSER] Ordered plain 1..N then BP-1..BP-N ({len(result)} cards)")
                        print(f"[PARSER] VALIDATION PASSED - keeping {len(result)} mixed base cards")
                        if result:
                            print(f"[PARSER] First card: {result[0].get('number')} {result[0].get('name')}")
                            print(f"[PARSER] Last card: {result[-1].get('number')} {result[-1].get('name')}")
                    elif has_prefix:
                        # Prefixed-only set (BD-/BDC-/etc.): all cards should be prefixed
                        invalid_cards = [c for c in result if '-' not in str(c.get('number', ''))]
                        if invalid_cards:
                            print(f"[PARSER] WARNING: Found {len(invalid_cards)} cards without prefixes in prefixed set!")
                            print(f"[PARSER] Removing invalid cards...")
                            result = [c for c in result if '-' in str(c.get('number', ''))]
                            print(f"[PARSER] Remaining cards: {len(result)}")
                        else:
                            print(f"[PARSER] VALIDATION PASSED - all {len(result)} prefixed cards are valid")
                            if result:
                                print(f"[PARSER] First card: {result[0].get('number')} {result[0].get('name')}")
                                print(f"[PARSER] Last card: {result[-1].get('number')} {result[-1].get('name')}")
                    else:
                        # Plain-numbered set: reject if any have prefixes or are not numeric
                        invalid_found = False
                        invalid_cards = []
                        for i, card in enumerate(result):
                            card_num = str(card.get('number', ''))
                            if '-' in card_num:
                                print(f"[PARSER] FATAL: Card #{i+1} has PREFIX: {card_num}")
                                print(f"[PARSER] Full card data: {card}")
                                invalid_cards.append((i+1, card_num, card))
                                invalid_found = True
                                if len(invalid_cards) >= 5:
                                    break
                            elif not card_num.isdigit():
                                print(f"[PARSER] FATAL: Card #{i+1} is NOT NUMERIC: {card_num}")
                                print(f"[PARSER] Full card data: {card}")
                                invalid_cards.append((i+1, card_num, card))
                                invalid_found = True
                                if len(invalid_cards) >= 5:
                                    break
                        
                        if invalid_found:
                            print(f"[PARSER] ========================================")
                            print(f"[PARSER] VALIDATION FAILED!")
                            print(f"[PARSER] Found {len(invalid_cards)} invalid cards:")
                            for idx, num, card in invalid_cards:
                                print(f"[PARSER]   Card #{idx}: {num} - {card.get('name')}")
                            print(f"[PARSER] REJECTING ALL {len(result)} CARDS - returning EMPTY list")
                            print(f"[PARSER] ========================================")
                            result = []
                        else:
                            print(f"[PARSER] VALIDATION PASSED - all {len(result)} cards are valid base cards")
                            if result:
                                print(f"[PARSER] First card: {result[0].get('number')} {result[0].get('name')}")
                                print(f"[PARSER] Last card: {result[-1].get('number')} {result[-1].get('name')}")
                    print(f"[PARSER] ========================================")
                
                # If Beckett fails, try Cardsmiths as backup (but ONLY if result is empty, not if it was rejected)
                if not result:
                    print("[PARSER] Base cards parser returned empty, trying Cardsmiths Breaks as backup...")
                    cardsmiths_url = self._convert_beckett_to_cardsmiths_url(url)
                    if cardsmiths_url:
                        result = self._fetch_base_cards_from_cardsmiths(cardsmiths_url)
                        print(f"[PARSER] Cardsmiths returned {len(result) if result else 0} cards")
                        # VALIDATE Cardsmiths result too - must be <= 300
                        if result and len(result) > 300:
                            print(f"[PARSER] ERROR: Cardsmiths returned {len(result)} cards (max 300)!")
                            result = []
                
                print(f"[PARSER] ========================================")
                print(f"[PARSER] RETURNING FROM fetch_from_beckett_url")
                print(f"[PARSER] Final result length: {len(result) if result else 0}")
                print(f"[PARSER] Returning tuple: (cards, description)")
                print(f"[PARSER] ========================================")
                return (result, description)
            elif checklist_type in ('prospects', 'bp', 'base_prospects', 'base-prospects'):
                print(f"[PARSER] ROUTING TO BASE PROSPECTS (BP-) PARSER")
                result = self._fetch_base_cards_from_beckett(url, soup=soup)
                result = self._split_bowman_base_vs_prospects(result, 'prospects')
                if result:
                    def _bp_key(card):
                        n = str(card.get('number', ''))
                        try:
                            return int(n.split('-', 1)[1])
                        except Exception:
                            return 9999
                    result = sorted(result, key=_bp_key)
                print(f"[PARSER] Prospects result: {len(result) if result else 0} BP- cards")
                return (result, description)
            elif checklist_type == 'inserts':
                cards = self._fetch_inserts_from_beckett(url, soup=soup)
                return (cards, description)
            elif checklist_type == 'parallels':
                cards = self._fetch_parallels_from_beckett(url, soup=soup)
                return (cards, description)
            elif checklist_type == 'autographs':
                # Use dedicated autograph parser
                cards = self._fetch_autographs_from_beckett(url, soup=soup)
                return (cards, description)
            elif checklist_type == 'numbered':
                # For #'ed cards, fetch all cards (base, inserts, autos) like parallels
                cards = self._fetch_parallels_from_beckett(url, soup=soup)
                return (cards, description)
            else:
                # Default to base cards
                cards = self._fetch_base_cards_from_beckett(url, soup=soup)
                return (cards, description)
        else:
            # Unknown URL - use universal parser that works with any site
            print(f"[PARSER] Universal parser - works with any URL")
            print(f"[PARSER] Checklist type: {checklist_type}")
            print(f"[PARSER] URL: {url}")
            # Route to appropriate parser based on type - pass soup to avoid re-fetching
            if checklist_type == 'base':
                result = self._fetch_base_cards_from_beckett(url, soup=soup)
                result = self._split_bowman_base_vs_prospects(result, 'base')
                return (result, description)
            elif checklist_type in ('prospects', 'bp', 'base_prospects', 'base-prospects'):
                result = self._fetch_base_cards_from_beckett(url, soup=soup)
                result = self._split_bowman_base_vs_prospects(result, 'prospects')
                return (result, description)
            elif checklist_type == 'inserts':
                cards = self._fetch_inserts_from_beckett(url, soup=soup)
                return (cards, description)
            elif checklist_type == 'parallels':
                cards = self._fetch_parallels_from_beckett(url, soup=soup)
                return (cards, description)
            elif checklist_type == 'autographs':
                # Use dedicated autograph parser
                cards = self._fetch_autographs_from_beckett(url, soup=soup)
                return (cards, description)
            elif checklist_type == 'numbered':
                # For #'ed cards, fetch all cards (base, inserts, autos) like parallels
                cards = self._fetch_parallels_from_beckett(url, soup=soup)
                return (cards, description)
            else:
                # Default to base cards
                cards = self._fetch_base_cards_from_beckett(url, soup=soup)
                return (cards, description)
    
    def _convert_beckett_to_cardsmiths_url(self, beckett_url: str) -> Optional[str]:
        """
        Attempt to convert a Beckett URL to a Cardsmiths Breaks URL format.
        Returns None if conversion is not possible.
        """
        try:
            # Extract set name from Beckett URL
            # Example: https://www.beckett.com/news/2025-26-topps-chrome-basketball-cards/
            # To: https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/
            
            # Try to extract the set identifier
            import re
            # Look for patterns like "2025-26-topps-chrome-basketball"
            match = re.search(r'/([^/]+-cards?)/?$', beckett_url)
            if match:
                set_identifier = match.group(1).replace('-cards', '').replace('-card', '')
                # Convert to Cardsmiths format
                cardsmiths_url = f"https://cardsmithsbreaks.com/full-checklist/{set_identifier}-hobby/"
                return cardsmiths_url
        except Exception as e:
            print(f"[PARSER] Could not convert URL: {e}")
        return None
    
    def _fetch_base_cards_from_cardboardconnection(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """Fetch base cards from Cardboard Connection - parses checklist tables."""
        cards = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            if soup is None:
                response = requests.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            
            tables = soup.find_all('table')
            seen_cards = set()
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 5:
                    continue
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        card_num = cells[0].get_text().strip()
                        player_name = cells[1].get_text().strip() if len(cells) > 1 else ''
                        team = cells[2].get_text().strip() if len(cells) > 2 else ''
                        if not card_num or not player_name:
                            continue
                        if not card_num.isdigit() and '-' not in card_num:
                            continue
                        try:
                            if card_num.isdigit() and int(card_num) > 500:
                                continue
                        except ValueError:
                            pass
                        card_key = (str(card_num), player_name.lower())
                        if card_key not in seen_cards and 2 <= len(player_name) <= 50:
                            seen_cards.add(card_key)
                            cards.append({
                                'number': card_num,
                                'name': player_name,
                                'team': team,
                                'set_name': url,
                                'type': 'base',
                                'rarity': 'Base'
                            })
            
            if cards:
                try:
                    def _cc_sort_key(c):
                        n = str(c.get('number', ''))
                        m = re.search(r'\d+', n)
                        return (int(m.group()) if m else 999, n)
                    cards.sort(key=_cc_sort_key)
                except Exception:
                    pass
            print(f"Found {len(cards)} base cards from Cardboard Connection")
        except Exception as e:
            print(f"Error fetching from Cardboard Connection: {e}")
        return cards
    
    def _fetch_base_cards_from_cardsmiths(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """Fetch base cards from Cardsmiths Breaks - parses table format."""
        cards = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            import time
            if soup is None:
                response = None
                for attempt in range(3):
                    try:
                        response = requests.get(url, headers=headers, timeout=60)
                        response.raise_for_status()
                        break
                    except (requests.exceptions.Timeout, requests.exceptions.RequestException):
                        if attempt < 2:
                            time.sleep(2)
                            continue
                        else:
                            raise
                
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the Base Cards section - look for table with base cards
            # The table has columns: #, Player, Team, Notes
            tables = soup.find_all('table')
            
            # Strategy 1: Find table with "Base Cards" heading
            base_table = None
            for table in tables:
                # Check if this is the base cards table
                # Look for "Base Cards" heading before the table
                prev_heading = table.find_previous(['h2', 'h3', 'h4', 'h5', 'strong', 'b', 'p'])
                if prev_heading:
                    heading_text = prev_heading.get_text().strip().lower()
                    if 'base' in heading_text and 'card' in heading_text and 'insert' not in heading_text:
                        base_table = table
                        break
            
            # Strategy 2: If no heading found, use the first large table (usually base cards)
            if not base_table:
                for table in tables:
                    rows = table.find_all('tr')
                    # Base cards table is usually the largest (200+ rows)
                    if len(rows) > 200:
                        # Check if first row has numeric card numbers
                        first_data_row = rows[1] if len(rows) > 1 else None
                        if first_data_row:
                            cells = first_data_row.find_all(['td', 'th'])
                            if len(cells) >= 3:
                                card_num = cells[0].get_text().strip()
                                if card_num.isdigit() and 1 <= int(card_num) <= 10:
                                    base_table = table
                                    break
            
            # Parse the base cards table
            if base_table:
                rows = base_table.find_all('tr')
                seen_cards = set()
                
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        card_num = cells[0].get_text().strip()
                        player_name = cells[1].get_text().strip()
                        team = cells[2].get_text().strip()
                        
                        # Skip if not a valid card number (base cards are numeric)
                        if not card_num or not card_num.isdigit():
                            continue
                        
                        # Skip if card number is too high
                        try:
                            if int(card_num) > 500:
                                continue
                        except:
                            continue
                        
                        # Basic validation
                        if (len(player_name) >= 2 and len(player_name) <= 50 and
                            len(team) >= 2 and len(team) <= 50):
                            
                            card_key = (card_num, player_name.lower())
                            if card_key not in seen_cards:
                                seen_cards.add(card_key)
                                cards.append({
                                    'number': card_num,
                                    'name': player_name,
                                    'team': team,
                                    'set_name': url,
                                    'type': 'base',
                                    'rarity': 'Base'
                                })
            
            # If no table found, try parsing from text (fallback)
            if not cards:
                text_content = soup.get_text()
                lines = text_content.split('\n')
                seen_cards = set()  # Reset for text parsing
                
                # Look for pattern: "1 Pascal Siakam, Indiana Pacers" or "| 1 | Pascal Siakam | Indiana Pacers |"
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try table row format: | 1 | Player Name | Team |
                    match = re.match(r'^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', line)
                    if match:
                        card_num, player_name, team = match.groups()
                        card_num = card_num.strip()
                        player_name = player_name.strip()
                        team = team.strip()
                        
                        # Skip if card number is too high
                        try:
                            if int(card_num) > 500:
                                continue
                        except:
                            continue
                        
                        if (len(player_name) >= 2 and len(player_name) <= 50 and
                            len(team) >= 2 and len(team) <= 50):
                            
                            card_key = (card_num, player_name.lower())
                            if card_key not in seen_cards:
                                seen_cards.add(card_key)
                                cards.append({
                                    'number': card_num,
                                    'name': player_name,
                                    'team': team,
                                    'set_name': url,
                                    'type': 'base',
                                    'rarity': 'Base'
                                })
            
            # Sort by card number
            try:
                cards.sort(key=lambda x: int(x['number']) if x['number'].isdigit() else 999)
            except:
                pass
            
            print(f"Found {len(cards)} base set cards from Cardsmiths Breaks")
            
            # CRITICAL: Cardsmiths must also return <= 300 cards for base set
            if len(cards) > 300:
                print(f"[CARDSMITHS] ERROR: Got {len(cards)} cards but base set should be max 300!")
                print(f"[CARDSMITHS] REJECTING ALL CARDS")
                return []
            
            # Validate no prefixed cards
            for card in cards:
                num = str(card.get('number', ''))
                if '-' in num:
                    print(f"[CARDSMITHS] ERROR: Found prefixed card: {card}")
                    return []
            
            return cards
            
        except Exception as e:
            print(f"Error fetching from Cardsmiths Breaks: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_all_sections_from_beckett(self, url: str, soup: BeautifulSoup = None) -> Dict[str, List[Dict]]:
        """
        Parse ALL cards from Beckett page and categorize by section.
        Returns a dict with keys: 'base', 'inserts', 'autographs', 'parallels'
        This is the correct approach - categorize by SECTION, not by format.
        Some sets (like Bowman Draft) have base cards with prefixes (BDP-1, BCP-1).
        """
        sections = {
            'base': [],
            'inserts': [],
            'autographs': [],
            'parallels': []
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            import time
            response = None
            for attempt in range(5):
                try:
                    response = requests.get(url, headers=headers, timeout=120)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 504:
                        if attempt < 4:
                            print(f"Beckett.com server timeout (504), retrying {attempt + 1}/5...")
                            time.sleep(5)
                            continue
                        else:
                            print("ERROR: Beckett.com server is timing out (504 Gateway Timeout)")
                            return sections
                    else:
                        response.raise_for_status()
                except requests.exceptions.Timeout:
                    if attempt < 4:
                        print(f"Request timeout, retrying {attempt + 1}/5...")
                        time.sleep(3)
                        continue
                    else:
                        print("ERROR: Request timed out after 5 attempts")
                        return sections
                except requests.exceptions.RequestException as e:
                    if attempt < 4:
                        print(f"Request error, retrying {attempt + 1}/5...")
                        time.sleep(3)
                        continue
                    else:
                        raise
            
            if not response or response.status_code != 200:
                print("ERROR: Could not fetch page from Beckett.com")
                return sections
            
            if soup is None:
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all section headings
            all_headings = []
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']):
                heading_text = heading.get_text().strip()
                all_headings.append((heading, heading_text.lower()))
            
            print(f"[PARSER] Found {len(all_headings)} headings on page")
            
            # Identify section boundaries
            section_boundaries = []
            for i, (heading, heading_lower) in enumerate(all_headings):
                section_type = None
                
                # Base Set section
                if ('base set' in heading_lower or 'base set checklist' in heading_lower) and \
                   'insert' not in heading_lower and 'parallel' not in heading_lower and \
                   'chrome' not in heading_lower and 'image' not in heading_lower and \
                   'etched' not in heading_lower:
                    section_type = 'base'
                
                # Inserts section - look for "Checklist – Inserts" or individual insert set names
                elif ('checklist – inserts' in heading_lower or 'checklist - inserts' in heading_lower or
                      ('insert' in heading_lower and 'base' not in heading_lower and 'parallel' not in heading_lower) or
                      # Individual insert set names (Bowman Draft specific)
                      any(insert_name in heading_lower for insert_name in [
                          'final draft', 'prized prospects', 'axis', 'bowman in action',
                          'bowman draft night', 'bowman spotlights', 'crystallized', 'dream draft pick'
                      ])):
                    section_type = 'inserts'
                
                # Autographs section
                elif any(keyword in heading_lower for keyword in ['autograph', 'signature', 'auto']):
                    section_type = 'autographs'
                
                # Parallels section
                elif 'parallel' in heading_lower and 'base' not in heading_lower:
                    section_type = 'parallels'
                
                if section_type:
                    heading_text_actual = heading.get_text().strip()
                    section_boundaries.append({
                        'type': section_type,
                        'heading': heading,
                        'heading_text': heading_text_actual,
                        'start_idx': i,
                        'end_idx': len(all_headings)  # Will be determined later
                    })
                    print(f"[PARSER] Found {section_type} section: {heading_text_actual}")
            
            # Now determine section boundaries - find where each section ends
            for i, section_info in enumerate(section_boundaries):
                # Find the next major section to determine where this one ends
                next_heading_idx = len(all_headings)
                for j in range(section_info['start_idx'] + 1, len(all_headings)):
                    next_heading_lower = all_headings[j][1]
                    # Stop at next major section (but allow insert set names to continue)
                    if section_info['type'] == 'inserts':
                        # For inserts, stop at major sections but allow other insert set names
                        is_insert_set_name = any(insert_name in next_heading_lower for insert_name in [
                            'final draft', 'prized prospects', 'axis', 'bowman in action',
                            'bowman draft night', 'bowman spotlights', 'crystallized', 'dream draft pick'
                        ])
                        if any(keyword in next_heading_lower for keyword in [
                            'base set', 'autograph', 'signature', 'parallel',
                            'numbered', 'refractor', 'team set', 'checklist top'
                        ]) and not is_insert_set_name:
                            next_heading_idx = j
                            break
                    else:
                        # For other sections, stop at next major section
                        if any(keyword in next_heading_lower for keyword in [
                            'base set', 'insert', 'autograph', 'signature', 'parallel',
                            'numbered', 'refractor', 'team set', 'checklist top'
                        ]):
                            next_heading_idx = j
                        break
                        
                section_info['end_idx'] = next_heading_idx
            
            # Parse cards from each section
            seen_cards = set()
            for section_info in section_boundaries:
                section_type = section_info['type']
                heading = section_info['heading']
                heading_text_actual = section_info['heading_text']
                
                # Debug sections
                if section_type == 'inserts':
                    print(f"[DEBUG] ========================================")
                    print(f"[DEBUG] PROCESSING INSERT SECTION: {heading_text_actual}")
                    print(f"[DEBUG] ========================================")
                elif section_type == 'autographs':
                    print(f"[DEBUG] ========================================")
                    print(f"[DEBUG] PROCESSING AUTOGRAPH SECTION: {heading_text_actual}")
                    print(f"[DEBUG] ========================================")
                
                # SIMPLIFIED APPROACH: Get all page text and find lines within this section
                # Similar to how base cards parser works - much more reliable
                page_text = soup.get_text()
                all_lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                
                # Find the heading line index - for inserts, verify card patterns exist nearby
                heading_text_lower = heading_text_actual.lower()
                heading_line_idx = None
                
                for i, line in enumerate(all_lines):
                    line_lower = line.lower()
                    # Match heading text
                    if heading_text_lower in line_lower and len(line) < 100:
                        # For insert/autograph sections, verify this heading has card data nearby
                        if section_type == 'inserts':
                            # Look ahead for card patterns (within next 30 lines)
                            found_cards_nearby = False
                            for j in range(i + 1, min(i + 30, len(all_lines))):
                                check_line = all_lines[j]
                                # Check for insert card patterns
                                if re.search(r'(FD-|PP-|A-|BIA-|BDN-|BS-|C-|79D-)', check_line):
                                    found_cards_nearby = True
                                    break
                            
                            if found_cards_nearby:
                                heading_line_idx = i
                                print(f"[DEBUG] Found heading '{heading_text_actual}' at line {i} with card data nearby")
                                break
                        elif section_type == 'autographs':
                            # Look ahead for autograph card patterns (within next 30 lines)
                            found_cards_nearby = False
                            autograph_pattern = r'(CPA-|DPPA-|AA-|PDA-|BIA-|PPA-|BDNA-|79D-|DPPBA-|BD-201)'
                            for j in range(i + 1, min(i + 30, len(all_lines))):
                                check_line = all_lines[j]
                                # Check for autograph card patterns
                                # Examples: CPA-AE, DPPBA-EW, DPPA-AE, BIA-BC, BD-201
                                # Exclude base card prefixes: BD- and BDC- (except BD-201)
                                if re.search(autograph_pattern, check_line):
                                    found_cards_nearby = True
                                    break
                            
                            if found_cards_nearby:
                                heading_line_idx = i
                                print(f"[DEBUG] [AUTO] Found heading '{heading_text_actual}' at line {i} with card data nearby")
                                break
                        else:
                            heading_line_idx = i
                            break
                    
                # Initialize content_lines
                content_lines = []
                
                if heading_line_idx is None:
                    if section_type == 'inserts':
                        print(f"[DEBUG] Could not find heading line with card data for: {heading_text_actual}")
                    elif section_type == 'autographs':
                        print(f"[DEBUG] [AUTO] Could not find heading line with card data for: {heading_text_actual}")
                    content_count = 0
                else:
                    # Collect lines after this heading - for inserts, only collect lines with card patterns
                    collecting = False
                    found_first_card = False
                    
                    for i in range(heading_line_idx, len(all_lines)):
                        line = all_lines[i]
                        line_lower = line.lower()
                        
                        # Start collecting after we find our heading
                        if i == heading_line_idx:
                            collecting = True
                            continue  # Skip the heading line itself
                    
                        if collecting:
                            # For inserts, only collect lines that contain card patterns
                            if section_type == 'inserts':
                                # Check if this line contains card patterns
                                has_card_pattern = bool(re.search(r'(FD-|PP-|A-|BIA-|BDN-|BS-|C-|79D-)', line))
                                
                                if has_card_pattern:
                                    found_first_card = True
                                    content_lines.append(line)
                                
                                # If we found cards, keep collecting until we hit a stopping condition
                                if found_first_card:
                                    # Stop at next major section heading
                                    is_insert_set_name = any(insert_name in line_lower for insert_name in [
                                        'final draft', 'prized prospects', 'axis', 'bowman in action',
                                        'bowman draft night', 'bowman spotlights', 'crystallized', 'dream draft pick'
                                    ])
                                    
                                    # Stop at major sections (not insert set names)
                                    if any(keyword in line_lower for keyword in [
                                        'base set', 'autograph', 'signature', 'parallel',
                                        'numbered', 'refractor', 'checklist top', 'team set'
                                    ]) and not is_insert_set_name and len(line) < 100:
                                        break
                                    
                                    # Stop at "Checklist Top" if it's a standalone line
                                    if 'checklist top' in line_lower and len(line) < 30:
                                        break
                                    
                                    # Also collect lines that might have card data (even if pattern not detected)
                                    # But skip obvious description lines
                                    if len(line) > 10 and not any(skip in line_lower for skip in [
                                        'cards per pack', 'packs per box', 'shop for', 'at a glance',
                                        'nfl hall of famer', 'bowman variety packs', 'will be rare'
                                    ]):
                                        # Only add if it looks like it might have card data
                                        if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', line):  # Has name-like pattern
                                            content_lines.append(line)
                                else:
                                    # Haven't found first card yet - skip description lines
                                    # Give up if we've gone too far (50 lines) without finding cards
                                    if i > heading_line_idx + 50:
                                        break
                            elif section_type == 'autographs':
                                # For autographs, only collect lines that contain autograph card patterns
                                # Only look for autograph-specific prefixes: CPA-, DPPA-, AA-, PDA-, BIA-, PPA-, BDNA-, 79D-, DPPBA-
                                # Special case: BD-201 (Retrofractor Autograph)
                                # Exclude base card prefixes: BD- and BDC- (except BD-201)
                                autograph_pattern = r'(CPA-|DPPA-|AA-|PDA-|BIA-|PPA-|BDNA-|79D-|DPPBA-|BD-201)'
                                has_card_pattern = bool(re.search(autograph_pattern, line))
                                
                                if has_card_pattern:
                                    found_first_card = True
                                    content_lines.append(line)
                                
                                # If we found cards, keep collecting until we hit a stopping condition
                                if found_first_card:
                                    # Stop at next major section heading
                                    if any(keyword in line_lower for keyword in [
                                        'base set', 'insert', 'parallel', 'numbered', 'refractor',
                                        'checklist top', 'team set'
                                    ]) and len(line) < 100:
                                        break
                                    
                                    # Stop at "Checklist Top" if it's a standalone line
                                    if 'checklist top' in line_lower and len(line) < 30:
                                        break
                                    
                                    # Continue collecting lines that contain autograph patterns
                                    # Also collect lines that might have card data (even if pattern not detected)
                                    # But skip obvious description lines
                                    if not has_card_pattern and len(line) > 10 and not any(skip in line_lower for skip in [
                                        'cards per pack', 'packs per box', 'shop for', 'at a glance',
                                        'nfl hall of famer', 'bowman variety packs', 'will be rare'
                                    ]):
                                        # Only add if it looks like it might have card data
                                        if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', line):  # Has name-like pattern
                                            content_lines.append(line)
                                else:
                                    # Haven't found first card yet - skip description lines
                                    # Give up if we've gone too far (50 lines) without finding cards
                                    if i > heading_line_idx + 50:
                                        break
                            else:
                                # For other sections, stop at next major heading
                                if any(keyword in line_lower for keyword in [
                                    'base set', 'insert', 'autograph', 'signature', 'parallel'
                                ]) and len(line) < 100:
                                    break
                    
                                # Add this line if it has content
                                if line and len(line) > 5:
                                    content_lines.append(line)
                    
                    # Convert lines to a single text block for parsing
                    content_to_parse = ['\n'.join(content_lines)] if content_lines else []
                    content_count = len(content_lines)
                
                if section_type == 'inserts':
                    print(f"[DEBUG] Collected {content_count} lines for section: {heading_text_actual}")
                elif section_type == 'autographs':
                    print(f"[DEBUG] [AUTO] Collected {content_count} lines for section: {heading_text_actual}")
                
                # Parse cards from this section
                cards_found_in_section = 0
                
                if section_type == 'inserts' and content_count > 0:
                    print(f"[DEBUG] First 5 lines:")
                    for i, line in enumerate(content_lines[:5]):
                        print(f"[DEBUG]   Line {i}: {repr(line[:150])}")
                    # Check if any line contains card prefixes
                    card_lines = [l for l in content_lines if any(prefix in l for prefix in ['FD-', 'PP-', 'A-', 'BIA-', 'BDN-', 'BS-', 'C-', '79D-'])]
                    if card_lines:
                        print(f"[DEBUG] Found {len(card_lines)} lines with card prefixes!")
                        for i, line in enumerate(card_lines[:3]):
                            print(f"[DEBUG]   Card line {i}: {repr(line[:200])}")
                
                # Process all collected lines
                section_stopped = False
                for line_idx, line in enumerate(content_lines):
                    if section_stopped:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    
                    line_lower = line.lower()
                    
                    # CRITICAL: Stop if we hit "Checklist Top" (Beckett section end marker)
                    # But only if it's a standalone line or button, not part of card text
                    if 'checklist top' in line_lower and (len(line) < 30 or line_lower == 'checklist top'):
                        print(f"[PARSER] Found 'Checklist Top' in line - end of {section_type} section")
                        section_stopped = True
                        break
                    
                    # Skip section headers and non-card content
                    if any(skip in line_lower for skip in [
                        'cards', 'checklist', 'shop for', 'team set', 'release date',
                        'cards per pack', 'packs per box', 'set size', 'what to expect'
                    ]) and len(line) < 50:
                        continue
                    
                    # Skip if line is just a small number
                    if line.isdigit() and int(line) < 100:
                        continue
                    
                    # CRITICAL: For Base Set, ONLY accept plain numbers (1-300)
                    # For Inserts, accept prefixed cards (YQ-1, SF-1, etc.)
                    card_num = None
                    player_name = None
                    team = None
                    
                    if section_type == 'base':
                        # Base Set: ONLY plain numbers, NO prefixes
                        # Pattern: "1 Player Name, Team" or "#1 Player Name, Team"
                        match = re.match(r'^#?(\d+)\s+([A-Za-z\s\'\-\u00C0-\u017F\.]+),\s*([A-Za-z\s\'\-\u00C0-\u017F\.]+?)(?:\s+RC)?$', line)
                        if match:
                            card_num_raw, player_name, team = match.groups()
                            card_num = card_num_raw.strip()
                            player_name = player_name.strip()
                            team = team.strip() if team else ''
                            
                            # Validate it's a base card number (1-300)
                            try:
                                num_val = int(card_num)
                                if num_val < 1 or num_val > 300:
                                    continue
                            except:
                                continue
                        else:
                            # Not a base card format - skip
                            continue
                    else:
                            # Inserts/Autographs/Parallels: Accept prefixed cards
                            # Cards may be on same line: "FD-1 Name, TeamFD-2 Name, Team"
                            # Use finditer to find all cards in the line
                            # Pattern: CODE-NUMBER Player Name, Team (e.g., "FD-1 Franklin Arias, Boston Red Sox")
                            # Or CODE-LETTERS for autographs (e.g., "BIA-BC Billy Carlson, Chicago White Sox")
                            # Allow 1-5 letters before dash (A-1, FD-1, BIA-1) or letter-letter (BIA-BC, PPA-BC) or special format (79D-DM)
                            if section_type == 'autographs':
                                # Autograph pattern: letters-letters (BIA-BC, PPA-BC, BDNA-EW, DPPBA-EW, DPPA-AE) or letters-number or special (79D-DM, BD-201)
                                # Allow up to 5 letters before dash and up to 5 letters after dash (e.g., DPPBA-EW)
                                # Cards may be concatenated: "BIA-BC Billy Carlson, Chicago White SoxBIA-CC Charlie Condon"
                                # CRITICAL: Team name must stop before next card prefix (e.g., stop before "BIA-CC" in "SoxBIA-CC")
                                # The team name capture must stop when it encounters a card prefix pattern (letters-dash-letters/numbers)
                                # Use a more sophisticated pattern that stops team name before next card prefix
                                # Pattern: CARD_CODE SPACE PLAYER_NAME COMMA TEAM_NAME (stop before next CARD_CODE or end)
                                # Team name can contain slashes for dual autos: "St. Louis Cardinals/Seattle Mariners"
                                # Pattern must handle:
                                # 1. Standard format: "BIA-BC Billy Carlson, Chicago White Sox"
                                # 2. Dual autos (no comma): "PDA-AD Liam Doyle/Kade Anderson St. Louis Cardinals/Seattle Mariners"
                                # 3. Cards concatenated without spaces: "SoxBIA-CC"
                                # Strategy: Match card code, then capture everything until next card code
                                # Cards may be concatenated: "SoxBIA-CC" or have space: "Sox BIA-CC"
                                # Pattern: CARD_CODE (space optional) CONTENT (stop before next CARD_CODE)
                                # Use non-greedy match to stop at the first next card code
                                # Only match autograph-specific prefixes: CPA-, DPPA-, AA-, PDA-, BIA-, PPA-, BDNA-, 79D-, DPPBA-
                                # Special case: BD-201 (Retrofractor Autograph)
                                # Exclude base card prefixes: BD- and BDC- (except BD-201)
                                pattern = r'((?:CPA|DPPA|AA|PDA|BIA|PPA|BDNA|79D|DPPBA)-\w+|BD-201)\s*(.+?)(?=(?:CPA|DPPA|AA|PDA|BIA|PPA|BDNA|79D|DPPBA)-\w+|BD-201|$)'
                            else:
                                # Insert pattern: letters-number (FD-1, PP-1, A-1) or special format (79D-DM)
                                pattern = r'([A-Z]{1,5}-\d+|\d+[A-Z]-[A-Z]+)\s+([A-Za-z\s\'\-\u00C0-\u017F\.]+?),\s*([A-Za-z\s\'\-\u00C0-\u017F\.]+?)(?=[A-Z]{1,5}-\d+|\d+[A-Z]-[A-Z]+|$)'
                            
                            # Debug for inserts
                            if section_type == 'inserts' and line_idx < 10 and any(prefix in line for prefix in ['FD-', 'PP-', 'A-', 'BIA-', 'BDN-', 'BS-', 'C-']):
                                print(f"[DEBUG] Line {line_idx} (length {len(line)}): {line[:150]}")
                            
                            matches = re.finditer(pattern, line)
                            found_any = False
                            match_count = 0
                            for match in matches:
                                match_count += 1
                                found_any = True
                                groups = match.groups()
                                card_num_raw = groups[0]
                                card_content = groups[1].strip() if len(groups) > 1 and groups[1] else ''
                                
                                card_num = card_num_raw.strip()
                                
                                # For autographs, filter out base card prefixes (BD-, BDC-)
                                # BD- and BDC- are base cards, not autographs
                                # Only accept autograph-specific prefixes: CPA-, DPPA-, AA-, PDA-, BIA-, PPA-, BDNA-, 79D-, DPPBA-
                                # Special case: BD-201 is a Retrofractor Autograph
                                if section_type == 'autographs':
                                    # Check if this is a base card prefix (BD- or BDC-)
                                    if card_num.startswith('BD-') or card_num.startswith('BDC-'):
                                        # Check if it's the special case BD-201 (Retrofractor Autograph)
                                        if card_num == 'BD-201':
                                            # This is a Retrofractor Autograph, allow it
                                            pass
                                        else:
                                            # This is a base card, skip it
                                            if line_idx < 5:
                                                print(f"[DEBUG] [AUTO] Skipping base card {card_num} (not an autograph)")
                                            continue
                                
                                # Parse the card content to extract player name and team
                                # Handle both formats:
                                # Standard: "Billy Carlson, Chicago White Sox"
                                # Dual auto: "Liam Doyle/Kade Anderson St. Louis Cardinals/Seattle Mariners"
                                if section_type == 'autographs' and card_content:
                                    # Try standard format first (has comma)
                                    comma_match = re.match(r'^(.+?),\s*(.+)$', card_content)
                                    if comma_match:
                                        player_name = comma_match.group(1).strip()
                                        team = comma_match.group(2).strip()
                                    else:
                                        # Try dual auto format (no comma, has slashes in team part)
                                        # Pattern: "Name1/Name2 Team1/Team2" where Team1/Team2 starts with capital
                                        dual_match = re.match(r'^(.+?)\s+([A-Z][a-zA-Z\s\.]+/[A-Z][a-zA-Z\s\.]+)$', card_content)
                                        if dual_match:
                                            player_name = dual_match.group(1).strip()
                                            team = dual_match.group(2).strip()
                                        else:
                                            # Fallback: treat entire content as player name
                                            player_name = card_content
                                            team = ''
                                else:
                                    # For non-autographs, use standard parsing
                                    comma_match = re.match(r'^(.+?),\s*(.+)$', card_content) if card_content else None
                                    if comma_match:
                                        player_name = comma_match.group(1).strip()
                                        team = comma_match.group(2).strip()
                                    else:
                                        player_name = card_content
                                        team = ''
                                
                                # For autographs, clean team name - remove any trailing card prefix that might have been captured
                                # Example: "Chicago White SoxBIA-CC" -> "Chicago White Sox"
                                if section_type == 'autographs' and team:
                                    # Remove any trailing autograph card prefix pattern (e.g., "BIA-CC", "PPA-BC", "BDNA-EW")
                                    # Only match autograph-specific prefixes: CPA-, DPPA-, AA-, PDA-, BIA-, PPA-, BDNA-, 79D-, DPPBA-
                                    # Also handle BD-201 (Retrofractor Autograph)
                                    autograph_prefix_pattern = r'(?:CPA|DPPA|AA|PDA|BIA|PPA|BDNA|79D|DPPBA)-\w+|BD-201'
                                    team = re.sub(autograph_prefix_pattern + r'$', '', team).strip()
                                    # Also check if team name contains an autograph card prefix pattern in the middle
                                    if re.search(autograph_prefix_pattern, team):
                                        # Split at the first occurrence of an autograph card prefix pattern
                                        team = re.split(autograph_prefix_pattern, team)[0].strip()
                                
                                # Process this card (will be validated below)
                                if card_num and player_name:
                                    # Validation
                                    if len(player_name) < 2 or len(player_name) > 50:
                                        continue
                                    if team and (len(team) < 2 or len(team) > 60):
                                        continue
                                    if re.search(r'/\d+', team):  # Skip numbered parallels
                                        continue
                                    
                                    # Extract numeric part for validation (skip special formats like 79D-DM or letter-letter formats)
                                    try:
                                        if '-' in card_num:
                                            num_part = card_num.split('-')[-1]
                                            # For autographs, allow letter-letter formats (BIA-BC, PPA-BC, CPA-AE, DPPBA-EW, etc.)
                                            if section_type == 'autographs' and num_part.isalpha():
                                                num_val = 1  # Valid - letter-letter format (will be sorted alphabetically)
                                            # Also allow numeric formats for autographs (e.g., BD-201)
                                            elif section_type == 'autographs' and num_part.isdigit():
                                                num_val = int(num_part)
                                                # For autographs, allow any number (some have numbers like BD-201)
                                                if num_val > 1000:
                                                    num_val = 1  # Still valid, just use 1 for sorting (will sort alphabetically)
                                            # Skip if it's not a number (e.g., "79D-DM")
                                            elif num_part.isdigit():
                                                num_val = int(num_part)
                                            else:
                                                # Special format like "79D-DM" - allow it
                                                num_val = 1  # Valid
                                        else:
                                            if section_type == 'autographs':
                                                # For autographs without dash, try to parse as number or allow as-is
                                                try:
                                                    num_val = int(card_num)
                                                except:
                                                    num_val = 1  # Allow non-numeric for autographs
                                            else:
                                                num_val = int(card_num)
                                        
                                        # For autographs, don't restrict by number range (they're sorted alphabetically)
                                        if section_type != 'autographs' and (num_val < 1 or num_val > 1000):
                                            continue
                                    except:
                                        # Allow special formats that don't have numeric parts (letter-letter, 79D-DM, etc.)
                                        if '-' in card_num:
                                            num_part = card_num.split('-')[-1]
                                            if section_type == 'autographs' and num_part.isalpha():
                                                pass  # Allow letter-letter format for autographs
                                            elif section_type == 'autographs' and num_part.isdigit():
                                                pass  # Allow numeric format for autographs (e.g., BD-201)
                                            elif not num_part.isdigit():
                                                pass  # Allow special formats like "79D-DM"
                                            else:
                                                continue
                                        else:
                                            if section_type == 'autographs':
                                                pass  # Allow non-numeric formats for autographs
                                            else:
                                                continue
                                    
                                    card_key = (card_num, player_name.lower(), section_type)
                                    if card_key not in seen_cards:
                                        seen_cards.add(card_key)
                                        card_data = {
                                            'number': card_num,
                                            'name': player_name,
                                            'team': team,
                                            'set_name': url,
                                            'type': section_type,
                                            'rarity': 'Base' if section_type == 'base' else section_type.title()
                                        }
                                        
                                        if section_type == 'inserts':
                                            # Extract insert name from prefix
                                            if '-' in card_num:
                                                card_data['insert_name'] = card_num.split('-')[0]
                                        
                                        sections[section_type].append(card_data)
                                        cards_found_in_section += 1
                                        if section_type == 'inserts':
                                            print(f"[DEBUG] ✓ Found insert card #{cards_found_in_section}: {card_num} {player_name}, {team}")
                                        if section_type == 'autographs':
                                            print(f"[DEBUG] ✓ Found autograph card #{cards_found_in_section}: {card_num} {player_name}, {team}")
                            
                            if section_type == 'inserts' and match_count > 0:
                                print(f"[DEBUG] Line {line_idx}: Found {match_count} card(s) via regex")
                            if section_type == 'autographs' and match_count > 0:
                                print(f"[DEBUG] [AUTO] Line {line_idx}: Found {match_count} card(s) via regex")
                            
                            if not found_any:
                                if section_type == 'inserts' and line_idx < 10 and any(prefix in line for prefix in ['FD-', 'PP-', 'A-', 'BIA-']):
                                    print(f"[DEBUG] Line {line_idx}: No regex matches (line length: {len(line)})")
                                    print(f"[DEBUG] Line content: {repr(line[:200])}")
                                if section_type == 'autographs' and line_idx < 10:
                                    print(f"[DEBUG] [AUTO] Line {line_idx}: No regex matches (line length: {len(line)})")
                                    print(f"[DEBUG] [AUTO] Line content: {repr(line[:200])}")
                                    # Try to see if there are card patterns in the line
                                    card_patterns = re.findall(r'[A-Z]{1,5}-[A-Z]{1,5}|[A-Z]{1,5}-\d+', line)
                                    if card_patterns:
                                        print(f"[DEBUG] [AUTO] Found card patterns in line: {card_patterns[:5]}")
                                        # Test the pattern
                                        test_matches = re.finditer(pattern, line)
                                        test_count = sum(1 for _ in test_matches)
                                        print(f"[DEBUG] [AUTO] Pattern matched {test_count} times")
                    
                    # Skip the old single-card processing below since we handled it above
                    continue
                    
                    # OLD CODE REMOVED - now handled above for inserts/autographs/parallels
                    # Base set cards are still processed below
                    if section_type == 'base' and card_num and player_name:
                        # Validation
                        if len(player_name) < 2 or len(player_name) > 50:
                            continue
                        if team and (len(team) < 2 or len(team) > 60):
                            continue
                        if re.search(r'/\d+', team):  # Skip numbered parallels
                            continue
                        
                        # Extract numeric part for validation
                        try:
                            if '-' in card_num:
                                num_part = card_num.split('-')[-1]
                                num_val = int(num_part)
                            else:
                                num_val = int(card_num)
                            
                            if num_val < 1 or num_val > 1000:
                                continue
                        except:
                            continue
                        
                        # CRITICAL: Stop parsing if we hit an insert set name in Base Set section
                        if any(insert_name in line_lower for insert_name in [
                            'youthquake', 'sleek finishers', 'destiny', 'instinct', 'voices',
                            'loading', 'generation rising', 'tall tales', 'clutch gene',
                            'xs and whoas', 'rock stars', 'let\'s go', 'ultra violet',
                            'radiating rookies', 'helix', 'go time', 'ball of duty',
                            'inspirational', 'activators', 'serenity', 'advisory',
                            'glass canvas', 'paradox', 'patented', 'fanatical', 'finals'
                        ]) and len(line) < 100:
                            print(f"[PARSER] Base Set stopped at insert set name: {line[:50]}")
                            section_stopped = True
                            break
                        
                        card_key = (card_num, player_name.lower(), section_type)
                        if card_key not in seen_cards:
                            seen_cards.add(card_key)
                            card_data = {
                                'number': card_num,
                                'name': player_name,
                                'team': team,
                                'set_name': url,
                                'type': section_type,
                                'rarity': 'Base' if section_type == 'base' else section_type.title()
                            }
                            
                            sections[section_type].append(card_data)
                            cards_found_in_section += 1
                            if section_type == 'inserts' and cards_found_in_section <= 5:
                                print(f"[PARSER] Found insert card: {card_num} {player_name}, {team}")
            
            # Sort each section
            for section_type in sections:
                if section_type == 'inserts':
                    # Sort by insert set (prefix) first, then by number within each set
                    # Define prefix order: FD-, PP-, A-, BIA-, BDN-, BS-, C-, 79D-
                    prefix_order = {
                        'FD': 1,   # Final Draft
                        'PP': 2,   # Prized Prospects
                        'A': 3,    # Axis
                        'BIA': 4,  # Bowman In Action
                        'BDN': 5,  # Bowman Draft Night
                        'BS': 6,   # Bowman Spotlights
                        'C': 7,    # Crystallized
                        '79D': 8,  # Dream Draft Pick
                    }
                    
                    def insert_sort_key(card):
                        num = str(card.get('number', ''))
                        try:
                            if '-' in num:
                                prefix = num.split('-')[0]
                                number_part = num.split('-', 1)[1]
                                # Extract numeric part (handle cases like "79D-DM")
                                num_match = re.search(r'\d+', number_part)
                                if num_match:
                                    num_val = int(num_match.group())
                                else:
                                    # Special format like "79D-DM" - use 0 for number
                                    num_val = 0
                                
                                # Get prefix order (default to 999 if unknown)
                                prefix_ord = prefix_order.get(prefix, 999)
                                
                                # Return tuple: (prefix_order, number)
                                return (prefix_ord, num_val)
                            elif num.isdigit():
                                return (999, int(num))  # Plain numbers go last
                            else:
                                match = re.search(r'\d+', num)
                                return (999, int(match.group()) if match else 999)
                        except:
                            return (999, 999)
                    
                    sections[section_type].sort(key=insert_sort_key)
                elif section_type == 'autographs':
                    # Sort autographs alphabetically by card number (since they don't have numeric ordering)
                    # Examples: CPA-AE, DPPBA-EW, BIA-BC - sort alphabetically
                    def autograph_sort_key(card):
                        num = str(card.get('number', ''))
                        # For autographs, sort by the full card number alphabetically
                        # This will group by prefix (CPA, DPPBA, etc.) and then by suffix
                        return num
                    sections[section_type].sort(key=autograph_sort_key)
                else:
                    # Sort by number
                    def sort_key(card):
                        num = str(card.get('number', ''))
                        try:
                            if '-' in num:
                                return int(num.split('-')[-1])
                            elif num.isdigit():
                                return int(num)
                            else:
                                match = re.search(r'\d+', num)
                                return int(match.group()) if match else 999
                        except:
                            return 999
                    sections[section_type].sort(key=sort_key)
            
            print(f"[PARSER] Parsed cards: Base={len(sections['base'])}, Inserts={len(sections['inserts'])}, "
                  f"Autographs={len(sections['autographs'])}, Parallels={len(sections['parallels'])}")
            if len(sections['inserts']) > 0:
                print(f"[PARSER] First 5 insert cards: {[c['number'] + ' ' + c['name'] for c in sections['inserts'][:5]]}")
            else:
                print(f"[DEBUG] ========================================")
                print(f"[DEBUG] NO INSERT CARDS FOUND!")
                print(f"[DEBUG] Total insert sections found: {len([s for s in section_boundaries if s['type'] == 'inserts'])}")
                print(f"[DEBUG] ========================================")
            
            return sections
            
        except Exception as e:
            print(f"Error parsing sections from Beckett: {e}")
            import traceback
            traceback.print_exc()
            return sections
    
    def _fetch_page_soup(self, url: str):
        """Fetch Beckett page HTML, preferring cloudscraper."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        import time
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            for attempt in range(3):
                try:
                    response = scraper.get(url, timeout=60)
                    if response.status_code == 200:
                        return BeautifulSoup(response.content, 'html.parser')
                    time.sleep(2)
                except Exception as e:
                    print(f"[NEW PARSER] cloudscraper error: {e}")
                    if attempt == 2:
                        break
                    time.sleep(2)
        except Exception as e:
            print(f"[NEW PARSER] cloudscraper unavailable: {e}")

        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=60, verify=False)
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                time.sleep(2)
            except Exception as e:
                print(f"[NEW PARSER] Request error: {e}")
                if attempt == 2:
                    return None
                time.sleep(2)
        return None

    def _parse_card_line_matches(self, line: str, mode: str = 'plain'):
        """Parse card entries from a line. mode is plain, BP, or BD."""
        results = []
        if mode == 'plain':
            pattern = r'(?<![A-Za-z0-9-])(\d{1,3})\s+([A-Z][^,\d]{1,60}?),\s*([^,\d]{1,80}?)(?:\s+RC)?(?=(?:(?<![A-Za-z0-9-])\d{1,3}\s+[A-Z])|[A-Z]{2,}-\d+|$)'
            for match in re.finditer(pattern, line):
                num = match.group(1).strip()
                name = match.group(2).strip()
                team = match.group(3).strip().rstrip('.,;:')
                if len(name) >= 2 and len(team) >= 2:
                    results.append((num, name, team))
        elif mode == 'BP':
            pattern = r'BP-(\d+)\s+([A-Z][^,\d]{1,60}?),\s*([^,\d]{1,80}?)(?=\s*BP-\d+|[A-Z]{2,}-\d+|$)'
            for match in re.finditer(pattern, line):
                num = match.group(1).strip()
                name = match.group(2).strip()
                team = match.group(3).strip().rstrip('.,;:')
                team = re.sub(r'BP-\d+.*$', '', team).strip()
                if len(name) >= 2 and len(team) >= 2:
                    results.append((f'BP-{num}', name, team))
        elif mode == 'BD':
            pattern = r'BDC?-(\d+)\s+(.+?)(?=BDC?-\d+|$)'
            for match in re.finditer(pattern, line):
                num = match.group(1).strip()
                content = match.group(2).strip()
                name_team = re.match(r'^([A-Z][^,\d]+?),\s*(.+?)$', content)
                if not name_team:
                    parts = content.split(',', 1)
                    if len(parts) != 2:
                        continue
                    name, team = parts[0].strip(), parts[1].strip()
                else:
                    name, team = name_team.group(1).strip(), name_team.group(2).strip()
                team = re.sub(r'BDC?-\d+.*$', '', team).strip()
                prefix = 'BDC-' if 'BDC-' in line[max(0, match.start()-5):match.start()+10] else 'BD-'
                if len(name) >= 2 and len(team) >= 2:
                    results.append((f'{prefix}{num}', name, team))
        return results

    def _slice_section_lines(self, lines, start_phrases, stop_phrases):
        """Return lines between first start heading and first stop heading."""
        start_idx = None
        for i, line in enumerate(lines):
            low = line.lower()
            if any(p in low for p in start_phrases):
                if len(line) < 120:
                    start_idx = i
                    break
        if start_idx is None:
            return []
        out = []
        for j in range(start_idx + 1, len(lines)):
            low = lines[j].lower()
            if any(p in low for p in stop_phrases) and len(lines[j]) < 120:
                break
            out.append(lines[j])
        return out


    def _split_bowman_base_vs_prospects(self, cards, checklist_type='base'):
        """For Bowman Baseball: Base = plain #s only; Prospects = BP-* only."""
        if not cards:
            return cards or []
        ctype = (checklist_type or 'base').lower()
        plain = [c for c in cards if str(c.get('number', '')).strip().isdigit()]
        bp = [c for c in cards if str(c.get('number', '')).strip().upper().startswith('BP-')]
        other_pref = [
            c for c in cards
            if '-' in str(c.get('number', ''))
            and not str(c.get('number', '')).strip().upper().startswith('BP-')
        ]
        mixed_bowman = bool(plain) and bool(bp) and not other_pref
        if ctype in ('prospects', 'bp', 'base_prospects', 'base-prospects'):
            print(f"[PARSER] Prospects mode: keeping {len(bp)} BP- cards (from {len(cards)} total)")
            return bp
        if mixed_bowman and ctype == 'base':
            print(f"[PARSER] Base Cards mode (Bowman): keeping {len(plain)} plain cards; dropping {len(bp)} BP-")
            return plain
        return cards

    def _fetch_base_cards_from_beckett(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """
        Beckett base parser.

        Supports plain numbers, BD/BDC draft prefixes, and Bowman Baseball
        veterans 1-N plus Base Prospects BP-1..BP-150 (before Chrome Prospects).
        """
        print(f"[NEW PARSER] ========================================")
        print(f"[NEW PARSER] STARTING BASE CARDS PARSER")
        print(f"[NEW PARSER] URL: {url}")
        print(f"[NEW PARSER] ========================================")

        cards = []
        try:
            if soup is None:
                soup = self._fetch_page_soup(url)
                if soup is None:
                    print("[NEW PARSER] Failed to fetch page")
                    return []

            page_text = soup.get_text('\n')
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            print(f"[NEW PARSER] Total lines: {len(lines)}")

            base_prefix = None
            for i, line in enumerate(lines):
                low = line.lower()
                if 'base set checklist' in low or low == 'base set':
                    for k in range(i + 1, min(i + 40, len(lines))):
                        if re.match(r'^1\s+[A-Z]', lines[k]):
                            base_prefix = None
                            print("[NEW PARSER] Detected PLAIN NUMBER format")
                            break
                        if re.match(r'^BDC?-\d+\s+[A-Z]', lines[k]):
                            base_prefix = 'BD-'
                            print("[NEW PARSER] Detected BD/BDC prefixed format")
                            break
                        m = re.match(r'^([A-Z]{2,})-\d+\s+[A-Z]', lines[k])
                        if m:
                            base_prefix = m.group(1) + '-'
                            print(f"[NEW PARSER] Detected PREFIXED format: {base_prefix}")
                            break
                    break

            seen = set()

            def add_card(number, name, team):
                if number in seen:
                    return
                if len(name) < 2 or len(team) < 2:
                    return
                seen.add(number)
                cards.append({
                    'number': number,
                    'name': name,
                    'team': team,
                    'set_name': url,
                    'type': 'base',
                    'rarity': 'Base',
                })

            if base_prefix == 'BD-':
                section = self._slice_section_lines(
                    lines,
                    start_phrases=['base set checklist', 'base set'],
                    stop_phrases=[
                        'autograph', 'insert', 'chrome prospects', 'parallels',
                        'team set', 'checklist top', 'master card list',
                    ],
                )
                for line in section:
                    for num, name, team in self._parse_card_line_matches(line, 'BD'):
                        add_card(num, name, team)
                print(f"[NEW PARSER] Collected {len(cards)} BD/BDC cards")
            elif base_prefix and base_prefix != 'BP-':
                escaped = re.escape(base_prefix)
                section = self._slice_section_lines(
                    lines,
                    start_phrases=['base set checklist', 'base set'],
                    stop_phrases=['autograph', 'insert', 'chrome prospects', 'parallels', 'team set', 'checklist top'],
                )
                pat = rf'{escaped}(\d+)\s+([A-Z][^,\d]+?),\s*([^,\d]+?)(?=\s*{escaped}\d+|{escaped}\d+|$)'
                for line in section:
                    for match in re.finditer(pat, line):
                        add_card(
                            f"{base_prefix}{match.group(1)}",
                            match.group(2).strip(),
                            match.group(3).strip().rstrip('.,;:'),
                        )
                print(f"[NEW PARSER] Collected {len(cards)} {base_prefix} cards")
            else:
                veteran_section = self._slice_section_lines(
                    lines,
                    start_phrases=['base set checklist'],
                    stop_phrases=[
                        'etched in glass', 'etched-in glass', 'base prospects',
                        'chrome prospects', 'red rc', 'variation', 'autograph',
                        'insert', 'checklist top', 'prospects',
                    ],
                )
                if not veteran_section:
                    veteran_section = self._slice_section_lines(
                        lines,
                        start_phrases=['base set'],
                        stop_phrases=[
                            'etched in glass', 'etched-in glass', 'base prospects',
                            'chrome prospects', 'variation', 'autograph', 'insert',
                            'checklist top', 'prospects',
                        ],
                    )
                for line in veteran_section:
                    for num, name, team in self._parse_card_line_matches(line, 'plain'):
                        try:
                            n = int(num)
                        except ValueError:
                            continue
                        if 1 <= n <= 300:
                            add_card(num, name, team)
                plain_count = len(cards)
                print(f"[NEW PARSER] Collected {plain_count} plain veteran base cards")

                prospect_section = self._slice_section_lines(
                    lines,
                    start_phrases=['base prospects'],
                    stop_phrases=[
                        'chrome prospects', 'autograph', 'insert', 'packfractor',
                        'etched in glass', 'checklist top', 'team set', 'master card',
                    ],
                )
                for line in prospect_section:
                    for num, name, team in self._parse_card_line_matches(line, 'BP'):
                        add_card(num, name, team)
                bp_count = len(cards) - plain_count
                print(f"[NEW PARSER] Collected {bp_count} BP- prospect base cards")

            def sort_key(card):
                # Plain veterans (1..N) first, then prefixed groups (BP-/BD-/BDC-) by prefix + number
                num = str(card['number'])
                if num.isdigit():
                    return (0, '', int(num))
                if '-' in num:
                    parts = num.split('-', 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        return (1, parts[0], int(parts[1]))
                return (2, num, 0)

            cards.sort(key=sort_key)
            print(
                f"[NEW PARSER] SUCCESS: Found {len(cards)} base cards "
                f"(range: {cards[0]['number'] if cards else 'N/A'} to {cards[-1]['number'] if cards else 'N/A'})"
            )
            if cards:
                print(f"[NEW PARSER] First: {cards[0]['number']} {cards[0]['name']}")
                print(f"[NEW PARSER] Last: {cards[-1]['number']} {cards[-1]['name']}")
            print(f"[NEW PARSER] ========================================")
            return cards

        except Exception as e:
            print(f"[NEW PARSER] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _fetch_autographs_from_beckett(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """
        DEDICATED AUTOGRAPH PARSER - Only handles autograph cards
        Extracts autograph cards with prefixes: CPA-, DPPA-, AA-, PDA-, BIA-, PPA-, BDNA-, 79D-, DPPBA-, BD-201
        Excludes base cards (BD- and BDC- except BD-201)
        """
        print(f"[AUTO PARSER] ========================================")
        print(f"[AUTO PARSER] STARTING DEDICATED AUTOGRAPH PARSER")
        print(f"[AUTO PARSER] URL: {url}")
        print(f"[AUTO PARSER] ========================================")
        
        cards = []
        
        try:
            # Fetch page if needed
            if soup is None:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                import time
                response = None
                for attempt in range(3):
                    try:
                        response = requests.get(url, headers=headers, timeout=60)
                        if response.status_code == 200:
                            break
                        time.sleep(2)
                    except Exception as e:
                        print(f"[AUTO PARSER] Request error: {e}")
                        if attempt == 2:
                            return []
                        time.sleep(2)
                
                if not response or response.status_code != 200:
                    print(f"[AUTO PARSER] Failed to fetch page")
                    return []
                
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get all text and split into lines
            page_text = soup.get_text()
            all_lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            
            # Find all autograph section headings
            all_headings = []
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']):
                heading_text = heading.get_text().strip()
                heading_lower = heading_text.lower()
                # Only look for autograph sections
                if any(keyword in heading_lower for keyword in ['autograph', 'signature', 'auto']):
                    all_headings.append((heading, heading_text, heading_lower))
            
            print(f"[AUTO PARSER] Found {len(all_headings)} autograph section headings")
            
            # Find heading line indices
            heading_line_indices = []
            for heading, heading_text, heading_lower in all_headings:
                # Find this heading in the lines
                for i, line in enumerate(all_lines):
                    if heading_lower in line.lower() and len(line) < 100:
                        # Verify autograph patterns exist nearby (within next 30 lines)
                        autograph_pattern = r'(CPA-|DPPA-|AA-|PDA-|BIA-|PPA-|BDNA-|79D-|DPPBA-|BD-201)'
                        found_cards_nearby = False
                        for j in range(i + 1, min(i + 30, len(all_lines))):
                            check_line = all_lines[j]
                            if re.search(autograph_pattern, check_line):
                                found_cards_nearby = True
                                break
                        
                        if found_cards_nearby:
                            heading_line_indices.append((i, heading_text))
                            print(f"[AUTO PARSER] Found heading '{heading_text}' at line {i} with card data nearby")
                            break
            
            # Collect and parse cards from each autograph section
            seen_cards = set()
            autograph_pattern = r'(CPA-|DPPA-|AA-|PDA-|BIA-|PPA-|BDNA-|79D-|DPPBA-|BD-201)'
            pattern = r'((?:CPA|DPPA|AA|PDA|BIA|PPA|BDNA|79D|DPPBA)-\w+|BD-201)\s*(.+?)(?=(?:CPA|DPPA|AA|PDA|BIA|PPA|BDNA|79D|DPPBA)-\w+|BD-201|$)'
            
            for heading_line_idx, heading_text in heading_line_indices:
                print(f"[AUTO PARSER] Processing section: {heading_text}")
                content_lines = []
                collecting = False
                found_first_card = False
                
                for i in range(heading_line_idx, len(all_lines)):
                    line = all_lines[i]
                    line_lower = line.lower()
                    
                    # Start collecting after we find our heading
                    if i == heading_line_idx:
                        collecting = True
                        continue  # Skip the heading line itself
                    
                    if collecting:
                        # Check for autograph card patterns
                        has_card_pattern = bool(re.search(autograph_pattern, line))
                        
                        if has_card_pattern:
                            found_first_card = True
                            content_lines.append(line)
                        
                        # If we found cards, keep collecting until we hit a stopping condition
                        if found_first_card:
                            # Stop at next major section heading
                            if any(keyword in line_lower for keyword in [
                                'base set', 'insert', 'parallel', 'numbered', 'refractor',
                                'checklist top', 'team set'
                            ]) and len(line) < 100:
                                break
                            
                            # Stop at "Checklist Top" if it's a standalone line
                            if 'checklist top' in line_lower and len(line) < 30:
                                break
                            
                            # Continue collecting lines that contain autograph patterns
                            if not has_card_pattern and len(line) > 10 and not any(skip in line_lower for skip in [
                                'cards per pack', 'packs per box', 'shop for', 'at a glance',
                                'nfl hall of famer', 'bowman variety packs', 'will be rare'
                            ]):
                                # Only add if it looks like it might have card data
                                if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', line):
                                    content_lines.append(line)
                        else:
                            # Haven't found first card yet - give up if we've gone too far
                            if i > heading_line_idx + 50:
                                break
                
                print(f"[AUTO PARSER] Collected {len(content_lines)} lines from section: {heading_text}")
                
                # Parse cards from collected lines
                for line_idx, line in enumerate(content_lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    line_lower = line.lower()
                    
                    # Stop if we hit "Checklist Top"
                    if 'checklist top' in line_lower and (len(line) < 30 or line_lower == 'checklist top'):
                        break
                    
                    # Skip section headers and non-card content
                    if any(skip in line_lower for skip in [
                        'cards', 'checklist', 'shop for', 'team set', 'release date',
                        'cards per pack', 'packs per box', 'set size', 'what to expect'
                    ]) and len(line) < 50:
                        continue
                    
                    # Parse autograph cards using regex
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        groups = match.groups()
                        card_num_raw = groups[0]
                        card_content = groups[1].strip() if len(groups) > 1 and groups[1] else ''
                        
                        card_num = card_num_raw.strip()
                        
                        # Filter out base card prefixes (BD- and BDC- except BD-201)
                        if card_num.startswith('BD-') or card_num.startswith('BDC-'):
                            if card_num != 'BD-201':
                                continue
                        
                        # Parse card content to extract player name and team
                        player_name = None
                        team = None
                        
                        if card_content:
                            # Try standard format first (has comma)
                            comma_match = re.match(r'^(.+?),\s*(.+)$', card_content)
                            if comma_match:
                                player_name = comma_match.group(1).strip()
                                team = comma_match.group(2).strip()
                            else:
                                # Try dual auto format (no comma, has slashes in team part)
                                dual_match = re.match(r'^(.+?)\s+([A-Z][a-zA-Z\s\.]+/[A-Z][a-zA-Z\s\.]+)$', card_content)
                                if dual_match:
                                    player_name = dual_match.group(1).strip()
                                    team = dual_match.group(2).strip()
                                else:
                                    # Fallback: treat entire content as player name
                                    player_name = card_content
                                    team = ''
                        
                        # Clean team name - remove any trailing autograph card prefix
                        if team:
                            autograph_prefix_pattern = r'(?:CPA|DPPA|AA|PDA|BIA|PPA|BDNA|79D|DPPBA)-\w+|BD-201'
                            team = re.sub(autograph_prefix_pattern + r'$', '', team).strip()
                            if re.search(autograph_prefix_pattern, team):
                                team = re.split(autograph_prefix_pattern, team)[0].strip()
                        
                        # Validate and add card
                        if card_num and player_name and len(player_name) >= 2 and len(player_name) <= 50:
                            if team and (len(team) < 2 or len(team) > 60):
                                continue
                            if re.search(r'/\d+', team):  # Skip numbered parallels
                                continue
                            
                            card_key = (card_num, player_name.lower(), 'autographs')
                            if card_key not in seen_cards:
                                seen_cards.add(card_key)
                                card_data = {
                                    'number': card_num,
                                    'name': player_name,
                                    'team': team,
                                    'set_name': url,
                                    'type': 'autographs',
                                    'rarity': 'Autographs'
                                }
                                cards.append(card_data)
                                if len(cards) <= 10:
                                    print(f"[AUTO PARSER] ✓ Found autograph card #{len(cards)}: {card_num} {player_name}, {team}")
            
            # Sort autographs alphabetically by card number
            def autograph_sort_key(card):
                return str(card.get('number', ''))
            
            cards.sort(key=autograph_sort_key)
            
            print(f"[AUTO PARSER] ========================================")
            print(f"[AUTO PARSER] SUCCESS: Found {len(cards)} autograph cards")
            print(f"[AUTO PARSER] ========================================")
            
            return cards
            
        except Exception as e:
            print(f"[AUTO PARSER] Error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _fetch_inserts_from_beckett(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """
        DEDICATED INSERT PARSER - Only handles insert cards
        Extracts insert cards with prefixes: FD-, PP-, A-, BIA-, BDN-, BS-, C-, 79D-
        """
        print(f"[INSERT PARSER] ========================================")
        print(f"[INSERT PARSER] STARTING DEDICATED INSERT PARSER")
        print(f"[INSERT PARSER] URL: {url}")
        print(f"[INSERT PARSER] ========================================")
        
        cards = []
        
        try:
            # Fetch page if needed
            if soup is None:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                import time
                response = None
                for attempt in range(3):
                    try:
                        response = requests.get(url, headers=headers, timeout=60)
                        if response.status_code == 200:
                            break
                        time.sleep(2)
                    except Exception as e:
                        print(f"[INSERT PARSER] Request error: {e}")
                        if attempt == 2:
                            return []
                        time.sleep(2)
                
                if not response or response.status_code != 200:
                    print(f"[INSERT PARSER] Failed to fetch page")
                    return []
                
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get all text and split into lines
            page_text = soup.get_text()
            all_lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            
            # Find all insert section headings
            all_headings = []
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']):
                heading_text = heading.get_text().strip()
                heading_lower = heading_text.lower()
                # Look for insert sections or individual insert set names
                if ('checklist – inserts' in heading_lower or 'checklist - inserts' in heading_lower or
                    ('insert' in heading_lower and 'base' not in heading_lower and 'parallel' not in heading_lower and 'autograph' not in heading_lower) or
                    any(insert_name in heading_lower for insert_name in [
                        'final draft', 'prized prospects', 'axis', 'bowman in action',
                        'bowman draft night', 'bowman spotlights', 'crystallized', 'dream draft pick'
                    ])):
                    all_headings.append((heading, heading_text, heading_lower))
            
            print(f"[INSERT PARSER] Found {len(all_headings)} insert section headings")
            
            # Find heading line indices
            heading_line_indices = []
            insert_pattern = r'(FD-|PP-|A-|BIA-|BDN-|BS-|C-|79D-)'
            for heading, heading_text, heading_lower in all_headings:
                # Find this heading in the lines
                for i, line in enumerate(all_lines):
                    if heading_lower in line.lower() and len(line) < 100:
                        # Verify insert patterns exist nearby (within next 30 lines)
                        found_cards_nearby = False
                        for j in range(i + 1, min(i + 30, len(all_lines))):
                            check_line = all_lines[j]
                            if re.search(insert_pattern, check_line):
                                found_cards_nearby = True
                                break
                        
                        if found_cards_nearby:
                            heading_line_indices.append((i, heading_text))
                            print(f"[INSERT PARSER] Found heading '{heading_text}' at line {i} with card data nearby")
                            break
            
            # Collect and parse cards from each insert section
            seen_cards = set()
            pattern = r'([A-Z]{1,5}-\d+|\d+[A-Z]-[A-Z]+)\s+([A-Za-z\s\'\-\u00C0-\u017F\.]+?),\s*([A-Za-z\s\'\-\u00C0-\u017F\.]+?)(?=[A-Z]{1,5}-\d+|\d+[A-Z]-[A-Z]+|$)'
            
            # Define prefix order for sorting
            prefix_order = {
                'FD': 1,   # Final Draft
                'PP': 2,   # Prized Prospects
                'A': 3,    # Axis
                'BIA': 4,  # Bowman In Action
                'BDN': 5,  # Bowman Draft Night
                'BS': 6,   # Bowman Spotlights
                'C': 7,    # Crystallized
                '79D': 8,  # Dream Draft Pick
            }
            
            def insert_sort_key(card):
                num = str(card.get('number', ''))
                try:
                    if '-' in num:
                        prefix = num.split('-')[0]
                        number_part = num.split('-', 1)[1]
                        num_match = re.search(r'\d+', number_part)
                        if num_match:
                            num_val = int(num_match.group())
                        else:
                            num_val = 0
                        prefix_ord = prefix_order.get(prefix, 999)
                        return (prefix_ord, num_val)
                    elif num.isdigit():
                        return (999, int(num))
                    else:
                        match = re.search(r'\d+', num)
                        return (999, int(match.group()) if match else 999)
                except:
                    return (999, 999)
            
            for heading_line_idx, heading_text in heading_line_indices:
                print(f"[INSERT PARSER] Processing section: {heading_text}")
                content_lines = []
                collecting = False
                found_first_card = False
                
                for i in range(heading_line_idx, len(all_lines)):
                    line = all_lines[i]
                    line_lower = line.lower()
                    
                    # Start collecting after we find our heading
                    if i == heading_line_idx:
                        collecting = True
                        continue  # Skip the heading line itself
                    
                    if collecting:
                        # Check for insert card patterns
                        has_card_pattern = bool(re.search(insert_pattern, line))
                        
                        if has_card_pattern:
                            found_first_card = True
                            content_lines.append(line)
                        
                        # If we found cards, keep collecting until we hit a stopping condition
                        if found_first_card:
                            # Check if this is another insert set name (allow it)
                            is_insert_set_name = any(insert_name in line_lower for insert_name in [
                                'final draft', 'prized prospects', 'axis', 'bowman in action',
                                'bowman draft night', 'bowman spotlights', 'crystallized', 'dream draft pick'
                            ])
                            
                            # Stop at major sections (not insert set names)
                            if any(keyword in line_lower for keyword in [
                                'base set', 'autograph', 'signature', 'parallel',
                                'numbered', 'refractor', 'checklist top', 'team set'
                            ]) and not is_insert_set_name and len(line) < 100:
                                break
                            
                            # Stop at "Checklist Top" if it's a standalone line
                            if 'checklist top' in line_lower and len(line) < 30:
                                break
                            
                            # Also collect lines that might have card data
                            if not has_card_pattern and len(line) > 10 and not any(skip in line_lower for skip in [
                                'cards per pack', 'packs per box', 'shop for', 'at a glance',
                                'nfl hall of famer', 'bowman variety packs', 'will be rare'
                            ]):
                                if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', line):
                                    content_lines.append(line)
                        else:
                            # Haven't found first card yet - give up if we've gone too far
                            if i > heading_line_idx + 50:
                                break
                
                print(f"[INSERT PARSER] Collected {len(content_lines)} lines from section: {heading_text}")
                
                # Parse cards from collected lines
                for line_idx, line in enumerate(content_lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    line_lower = line.lower()
                    
                    # Stop if we hit "Checklist Top"
                    if 'checklist top' in line_lower and (len(line) < 30 or line_lower == 'checklist top'):
                        break
                    
                    # Skip section headers and non-card content
                    if any(skip in line_lower for skip in [
                        'cards', 'checklist', 'shop for', 'team set', 'release date',
                        'cards per pack', 'packs per box', 'set size', 'what to expect'
                    ]) and len(line) < 50:
                        continue
                    
                    # Parse insert cards using regex
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        groups = match.groups()
                        card_num_raw = groups[0]
                        player_name = groups[1].strip() if len(groups) > 1 and groups[1] else ''
                        team = groups[2].strip() if len(groups) > 2 and groups[2] else ''
                        
                        card_num = card_num_raw.strip()
                        
                        # Validate and add card
                        if card_num and player_name and len(player_name) >= 2 and len(player_name) <= 50:
                            if team and (len(team) < 2 or len(team) > 60):
                                continue
                            if re.search(r'/\d+', team):  # Skip numbered parallels
                                continue
                            
                            # Extract numeric part for validation
                            try:
                                if '-' in card_num:
                                    num_part = card_num.split('-')[-1]
                                    if num_part.isdigit():
                                        num_val = int(num_part)
                                        if num_val < 1 or num_val > 1000:
                                            continue
                                    else:
                                        # Special format like "79D-DM" - allow it
                                        pass
                                else:
                                    num_val = int(card_num)
                                    if num_val < 1 or num_val > 1000:
                                        continue
                            except:
                                # Allow special formats
                                pass
                            
                            card_key = (card_num, player_name.lower(), 'inserts')
                            if card_key not in seen_cards:
                                seen_cards.add(card_key)
                                card_data = {
                                    'number': card_num,
                                    'name': player_name,
                                    'team': team,
                                    'set_name': url,
                                    'type': 'inserts',
                                    'rarity': 'Inserts'
                                }
                                
                                # Extract insert name from prefix
                                if '-' in card_num:
                                    card_data['insert_name'] = card_num.split('-')[0]
                                
                                cards.append(card_data)
                                if len(cards) <= 10:
                                    print(f"[INSERT PARSER] ✓ Found insert card #{len(cards)}: {card_num} {player_name}, {team}")
            
            # Sort inserts by prefix order, then by number
            cards.sort(key=insert_sort_key)
            
            print(f"[INSERT PARSER] ========================================")
            print(f"[INSERT PARSER] SUCCESS: Found {len(cards)} insert cards")
            print(f"[INSERT PARSER] ========================================")
            
            return cards
            
        except Exception as e:
            print(f"[INSERT PARSER] Error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _fetch_parallels_from_beckett(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """
        Fetch ALL cards (base + inserts + autos) for parallels.
        Returns cards with parallel_type information extracted from the page.
        User will select which parallel type to list via dropdown.
        """
        cards = []
        
        try:
            # Use provided soup if available, otherwise fetch
            if soup is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                import time
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.get(url, headers=headers, timeout=60)
                        response.raise_for_status()
                        break
                    except requests.exceptions.Timeout:
                        if attempt < max_retries - 1:
                            print(f"[DEBUG] Timeout on attempt {attempt + 1}, retrying...")
                            time.sleep(2)
                            continue
                        else:
                            raise
                    except requests.exceptions.RequestException as e:
                        if attempt < max_retries - 1:
                            print(f"[DEBUG] Request error on attempt {attempt + 1}: {e}, retrying...")
                            time.sleep(2)
                            continue
                        else:
                            raise
                soup = BeautifulSoup(response.content, 'html.parser')
            
            seen_cards = set()
            
            # CRITICAL: For parallels, we need ALL cards from THIS SET ONLY
            # Make sure we're only getting cards from the current URL/page
            
            print(f"[PARSER] [PARALLELS] Starting parallel card fetch from: {url}")
            
            # Step 1: Get all base cards from THIS page only
            print("[PARSER] [PARALLELS] Step 1: Fetching base cards...")
            base_cards = self._fetch_base_cards_from_beckett(url, soup=soup)
            print(f"[PARSER] [PARALLELS] Found {len(base_cards)} base cards")
            for card in base_cards:
                # Verify card is from this set (check set_name matches URL)
                if card.get('set_name') == url or not card.get('set_name'):
                    card_key = (card.get('number', ''), card.get('name', '').lower())
                    if card_key not in seen_cards:
                        seen_cards.add(card_key)
                        card['parallel_type'] = ''
                        card['numbering'] = ''
                        cards.append(card)
            
            # Step 2: Get all insert cards from THIS page only
            print("[PARSER] [PARALLELS] Step 2: Fetching insert cards...")
            insert_cards = self._fetch_inserts_from_beckett(url, soup=soup)
            print(f"[PARSER] [PARALLELS] Found {len(insert_cards)} insert cards")
            for card in insert_cards:
                # Verify card is from this set
                if card.get('set_name') == url or not card.get('set_name'):
                    card_key = (card.get('number', ''), card.get('name', '').lower())
                    if card_key not in seen_cards:
                        seen_cards.add(card_key)
                        card['parallel_type'] = ''
                        card['numbering'] = ''
                        cards.append(card)
            
            # Step 3: Get all numbered/auto cards from THIS page only
            print("[PARSER] [PARALLELS] Step 3: Fetching numbered/auto cards...")
            numbered_cards = self._fetch_numbered_autos_from_beckett(url, soup=soup)
            print(f"[PARSER] [PARALLELS] Found {len(numbered_cards)} numbered/auto cards")
            for card in numbered_cards:
                # Verify card is from this set
                if card.get('set_name') == url or not card.get('set_name'):
                    card_key = (card.get('number', ''), card.get('name', '').lower())
                    if card_key not in seen_cards:
                        seen_cards.add(card_key)
                        card['parallel_type'] = ''
                        card['numbering'] = ''
                        cards.append(card)
            
            # Step 4: Extract parallel types from the "Parallels" section
            print("[PARSER] Extracting parallel types from checklist...")
            parallel_types = self._extract_parallel_types(soup)
            
            # Add parallel type info to all cards
            for card in cards:
                if not card.get('parallel_types'):
                    card['parallel_types'] = parallel_types  # Store all available parallel types
            
            print(f"Found {len(cards)} total cards for parallels")
            print(f"Available parallel types: {', '.join(parallel_types[:10])}..." if len(parallel_types) > 10 else f"Available parallel types: {', '.join(parallel_types)}")
            return cards
            
        except Exception as e:
            print(f"Error fetching parallels from Beckett: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_parallel_types(self, soup: BeautifulSoup) -> List[str]:
        """Extract all parallel types from the checklist page."""
        parallel_types = []
        seen_types = set()
        
        # Find the "Parallels" section
        parallels_section = None
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']):
            heading_text = heading.get_text().strip().lower()
            if 'parallel' in heading_text or 'refractor' in heading_text:
                if 'base set' not in heading_text:
                    parallels_section = heading
                    print(f"[PARSER] Found Parallels section: {heading.get_text().strip()}")
                    break
        
        if not parallels_section:
            # Fallback: search entire page
            text_content = soup.get_text()
        else:
            # Get content from parallels section
            text_content = ""
            current = parallels_section.next_sibling
            while current:
                if hasattr(current, 'get_text'):
                    text_content += current.get_text() + "\n"
                current = current.next_sibling
        
        # Extract parallel type names (e.g., "Refractors Green /99", "Refractors Gold /50")
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Skip if it's a card entry (has player name pattern)
            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', line):  # Likely a player name
                continue
            
            # Match parallel type patterns
            # Examples: "Refractors Green /99", "Refractors Gold /50", "X-Fractors", etc.
            if any(keyword in line_lower for keyword in [
                'refractor', 'parallel', 'geometric', 'aqua', 'blue', 'green',
                'purple', 'gold', 'orange', 'red', 'white', 'black', 'superfractor',
                'raywave', 'pulsar', 'magenta', 'teal', 'yellow', 'x-fractor',
                'frozenfractor', 'speckle', 'wave', 'basketball', 'lightboard'
            ]):
                # Clean up the line
                parallel_type = line.strip()
                # Remove common prefixes/suffixes
                parallel_type = re.sub(r'^refractors?\s+', '', parallel_type, flags=re.I)
                parallel_type = re.sub(r'\s*/\d+$', '', parallel_type)  # Remove /99, /50, etc.
                parallel_type = parallel_type.strip()
                
                if parallel_type and len(parallel_type) > 2 and parallel_type not in seen_types:
                    seen_types.add(parallel_type)
                    parallel_types.append(parallel_type)
        
        # Also look for numbered parallels (e.g., "/99", "/50")
        numbered_patterns = re.findall(r'/(\d+)', text_content)
        for num in numbered_patterns:
            if num not in ['1', '2', '3', '4', '5']:  # Skip small numbers (likely card numbers)
                type_name = f"/{num}"
                if type_name not in seen_types:
                    seen_types.add(type_name)
                    parallel_types.append(type_name)
        
        return sorted(parallel_types)
    
    def _fetch_numbered_autos_from_beckett(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """Fetch ONLY numbered cards and autographs from Beckett.
        For now, uses the autograph parser since numbered cards are typically autographs."""
        # Use the dedicated autograph parser
        return self._fetch_autographs_from_beckett(url, soup=soup)
    
    def _fetch_parallels_from_beckett(self, url: str, soup: BeautifulSoup = None) -> List[Dict]:
        """
        Fetch ALL cards (base + inserts + autos) for parallels.
        Returns cards with parallel_type information extracted from the page.
        User will select which parallel type to list via dropdown.
        """
        cards = []
        
        try:
            # Use provided soup if available, otherwise fetch
            if soup is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                import time
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.get(url, headers=headers, timeout=60)
                        response.raise_for_status()
                        break
                    except requests.exceptions.Timeout:
                        if attempt < max_retries - 1:
                            print(f"[DEBUG] Timeout on attempt {attempt + 1}, retrying...")
                            time.sleep(2)
                            continue
                        else:
                            raise
                    except requests.exceptions.RequestException as e:
                        if attempt < max_retries - 1:
                            print(f"[DEBUG] Request error on attempt {attempt + 1}: {e}, retrying...")
                            time.sleep(2)
                            continue
                        else:
                            raise
                soup = BeautifulSoup(response.content, 'html.parser')
            
            seen_cards = set()
            
            # CRITICAL: For parallels, we need ALL cards from THIS SET ONLY
            # Make sure we're only getting cards from the current URL/page
            
            print(f"[PARSER] [PARALLELS] Starting parallel card fetch from: {url}")
                
            # Step 1: Get all base cards from THIS page only
            print("[PARSER] [PARALLELS] Step 1: Fetching base cards...")
            base_cards = self._fetch_base_cards_from_beckett(url, soup=soup)
            print(f"[PARSER] [PARALLELS] Found {len(base_cards)} base cards")
            for card in base_cards:
                # Verify card is from this set (check set_name matches URL)
                if card.get('set_name') == url or not card.get('set_name'):
                    card_key = (card.get('number', ''), card.get('name', '').lower())
                    if card_key not in seen_cards:
                        seen_cards.add(card_key)
                        card['parallel_type'] = ''
                        card['numbering'] = ''
                        cards.append(card)
                    
            # Step 2: Get all insert cards from THIS page only
            print("[PARSER] [PARALLELS] Step 2: Fetching insert cards...")
            insert_cards = self._fetch_inserts_from_beckett(url, soup=soup)
            print(f"[PARSER] [PARALLELS] Found {len(insert_cards)} insert cards")
            for card in insert_cards:
                # Verify card is from this set
                if card.get('set_name') == url or not card.get('set_name'):
                    card_key = (card.get('number', ''), card.get('name', '').lower())
                    if card_key not in seen_cards:
                        seen_cards.add(card_key)
                        card['parallel_type'] = ''
                        card['numbering'] = ''
                        cards.append(card)
            
            # Step 3: Get all numbered/auto cards from THIS page only
            print("[PARSER] [PARALLELS] Step 3: Fetching numbered/auto cards...")
            numbered_cards = self._fetch_numbered_autos_from_beckett(url, soup=soup)
            print(f"[PARSER] [PARALLELS] Found {len(numbered_cards)} numbered/auto cards")
            for card in numbered_cards:
                # Verify card is from this set
                if card.get('set_name') == url or not card.get('set_name'):
                    card_key = (card.get('number', ''), card.get('name', '').lower())
                    if card_key not in seen_cards:
                        seen_cards.add(card_key)
                        card['parallel_type'] = ''
                        card['numbering'] = ''
                        cards.append(card)
            
            # Step 4: Extract parallel types from the "Parallels" section
            print("[PARSER] Extracting parallel types from checklist...")
            parallel_types = self._extract_parallel_types(soup)
            
            # Add parallel type info to all cards
            for card in cards:
                if not card.get('parallel_types'):
                    card['parallel_types'] = parallel_types  # Store all available parallel types
            
            print(f"Found {len(cards)} total cards for parallels")
            print(f"Available parallel types: {', '.join(parallel_types[:10])}..." if len(parallel_types) > 10 else f"Available parallel types: {', '.join(parallel_types)}")
            return cards
            
        except Exception as e:
            print(f"Error fetching parallels from Beckett: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_parallel_types(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all parallel types from the checklist page.
        Parallels are typically listed above each set section like:
        "Parallels Refractor /250 Mini-Diamond /150 Green Refractor /99 Gold Refractor /50..."
        Returns list of formatted parallel types like "Orange Refractor /25"
        """
        parallel_types = []
        seen_types = set()
        
        # Get all text from the page
        all_text = soup.get_text()
        all_lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        
        print(f"[PARSER] [PARALLELS] Extracting parallel types from {len(all_lines)} lines...")
        
        # Look for parallel information above each set section
        # Pattern: "Parallels Refractor /250 Mini-Diamond /150 Green Refractor /99..."
        # or "Parallels Red Refractor /5 Superfractor /1"
        parallel_pattern = r'(?:Parallels?\s+)?([A-Za-z\s\-]+?)\s*/\s*(\d+)'
        
        for i, line in enumerate(all_lines):
            line_lower = line.lower()
            
            # Look for lines that mention parallels/refractors but aren't card entries
            if ('parallel' in line_lower or 'refractor' in line_lower) and \
               not re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+,\s+[A-Z]', line):  # Not a card entry
                
                # Extract all parallel type patterns from this line
                # Match patterns like "Refractor /250", "Green Refractor /99", "Orange Refractor /25"
                matches = re.finditer(r'([A-Za-z\s\-]+?)\s*/\s*(\d+)', line)
                
                for match in matches:
                    parallel_name = match.group(1).strip()
                    numbering = match.group(2).strip()
                    
                    # Clean up the parallel name
                    parallel_name = re.sub(r'^parallels?\s+', '', parallel_name, flags=re.I).strip()
                    parallel_name = re.sub(r'\s+', ' ', parallel_name)  # Normalize spaces
                    
                    # Skip if it's too short or looks like a card number
                    if len(parallel_name) < 2 or parallel_name.isdigit():
                        continue
                    
                    # Format: "Orange Refractor /25"
                    formatted_type = f"{parallel_name} /{numbering}"
                    
                    if formatted_type not in seen_types and len(parallel_name) > 2:
                        seen_types.add(formatted_type)
                        parallel_types.append(formatted_type)
                        print(f"[PARSER] [PARALLELS] Found parallel type: {formatted_type}")
        
        # Also look for standalone numbered patterns that might have been missed
        # Look for patterns like "/250", "/150", "/99" near parallel keywords
        for i, line in enumerate(all_lines):
            line_lower = line.lower()
            if 'parallel' in line_lower or 'refractor' in line_lower:
                # Find all /number patterns in this line
                numbered_matches = re.finditer(r'/\s*(\d+)', line)
                for match in numbered_matches:
                    num = match.group(1)
                    # Get context around the number (20 chars before)
                    start = max(0, match.start() - 20)
                    context = line[start:match.start()].strip()
                    
                    # If context looks like a parallel name, create formatted type
                    if context and not re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+,\s+[A-Z]', context):
                        # Try to extract a meaningful name from context
                        context_clean = re.sub(r'^parallels?\s+', '', context, flags=re.I).strip()
                        if context_clean and len(context_clean) > 2:
                            formatted_type = f"{context_clean} /{num}"
                            if formatted_type not in seen_types:
                                seen_types.add(formatted_type)
                                parallel_types.append(formatted_type)
                                print(f"[PARSER] [PARALLELS] Found parallel type from context: {formatted_type}")
        
        # Sort by numbering (lower numbers first, then alphabetically)
        def sort_key(pt):
            # Extract number from "/25" format
            num_match = re.search(r'/(\d+)$', pt)
            if num_match:
                return (int(num_match.group(1)), pt)
            return (999999, pt)  # Put unnumbered at end
        
        parallel_types_sorted = sorted(parallel_types, key=sort_key)
        
        print(f"[PARSER] [PARALLELS] Extracted {len(parallel_types_sorted)} parallel types")
        return parallel_types_sorted
    
    def _fetch_custom(self, set_name: str) -> List[Dict]:
        """Custom fetch method - can be extended for other sources."""
        # This is a placeholder for custom implementations
        # You can add database queries, web scraping, etc.
        print(f"Custom fetch not implemented for set: {set_name}")
        return []
    
    def search_set(self, query: str) -> List[Dict]:
        """Search for sets matching a query."""
        if self.source == 'scryfall':
            url = "https://api.scryfall.com/sets"
            response = requests.get(url)
            response.raise_for_status()
            sets = response.json().get('data', [])
            return [s for s in sets if query.lower() in s.get('name', '').lower()]
        # Add other sources as needed
        return []
