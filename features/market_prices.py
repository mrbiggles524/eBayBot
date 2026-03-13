"""Market price lookup from eBay sold listings. v4.010 - SerpAPI primary (works), eBay scrape fallback."""
import os
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import cloudscraper
    _HAS_CLOUDSCRAPER = True
except ImportError:
    _HAS_CLOUDSCRAPER = False

_SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '').strip()


class MarketPriceLookup:
    """Simple eBay sold scrape. Returns _debug when no results."""
    
    def __init__(self):
        self._req_session = requests.Session()
        self._req_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.ebay.com/',
        })
        self._cloud = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}) if _HAS_CLOUDSCRAPER else None
    
    def get_ebay_sold_prices(
        self,
        player_name: str,
        set_name: str,
        card_number: Optional[str] = None,
        parallel_type: Optional[str] = None,
        max_results: int = 15,
        include_debug: bool = True
    ) -> Dict:
        """
        Simple eBay sold scrape. Median as suggested. Kon->Kon Knueppel.
        Returns _debug when no results (status, html_len, block, s_item_count).
        """
        if not player_name or not player_name.strip():
            return self._empty()
        
        player_name = player_name.strip()
        KNOWN_ABBREVS = {'kon': 'Kon Knueppel', 'k2': 'Kon Knueppel'}
        if player_name.lower() in KNOWN_ABBREVS:
            player_name = KNOWN_ABBREVS[player_name.lower()]
        
        set_short = (set_name or '').strip()[:40] if set_name else ''
        query = f"{player_name} {set_short} card" if set_short else f"{player_name} basketball card"
        if card_number and str(card_number).strip():
            query += f" #{card_number}"
        
        result = self._empty()
        debug_log = []
        
        def _extract_prices(html: str) -> List[float]:
            out = []
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select('.s-item')[1:max_results + 15]
            for item in items:
                span = item.select_one('.s-item__price')
                if span:
                    text = span.get_text(strip=True)
                    nums = re.findall(r'\$[\d,]+\.?\d*', text.replace(',', ''))
                    vals = []
                    for m in nums:
                        try:
                            p = float(m.replace('$', '').replace(',', ''))
                            if 0.25 < p < 5000:
                                vals.append(p)
                        except (ValueError, TypeError):
                            pass
                    if vals:
                        out.append(max(vals) if ' to ' in text.lower() and len(vals) > 1 else vals[0])
            if len(out) < 3:
                for tag in soup.find_all(string=re.compile(r'\$\d')):
                    for m in re.finditer(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.\d{2})', str(tag)):
                        try:
                            p = float(m.group(1).replace(',', ''))
                            if 0.50 < p < 500 and p not in (0.01, 0.99, 1.0):
                                out.append(p)
                                if len(out) >= max_results:
                                    break
                        except (ValueError, TypeError):
                            pass
            return out
        
        def _fetch_ebay(url: str, label: str, use_cloud: bool = False) -> List[float]:
            sess = self._cloud if (use_cloud and self._cloud) else self._req_session
            try:
                r = sess.get(url, timeout=8 if use_cloud else 5)
                html = r.text
                block = 'pardon our interruption' in html.lower() or 'captcha' in html.lower()
                s_count = len(BeautifulSoup(html, 'html.parser').select('.s-item'))
                prices = [] if block else _extract_prices(html)
                if include_debug:
                    debug_log.append(f"{label}{'(cloud)' if use_cloud else ''}: status={r.status_code} len={len(html)} block={block} s_items={s_count} prices={len(prices)}")
                if block:
                    return []
                return prices
            except Exception as e:
                if include_debug:
                    debug_log.append(f"{label}{'(cloud)' if use_cloud else ''}: {type(e).__name__}: {str(e)[:60]}")
                return []
        
        def _fetch_serpapi(q: str) -> List[float]:
            if not _SERPAPI_KEY:
                return []
            try:
                r = self._req_session.get('https://serpapi.com/search.json', params={
                    'engine': 'ebay', '_nkw': q, 'ebay_domain': 'ebay.com', 'show_only': 'Sold', 'api_key': _SERPAPI_KEY
                }, timeout=10)
                if r.status_code != 200:
                    if include_debug:
                        debug_log.append(f"serpapi: status={r.status_code}")
                    return []
                results = (r.json() or {}).get('organic_results') or []
                out = []
                for item in results[:15]:
                    pobj = item.get('price')
                    val = None
                    if isinstance(pobj, dict) and 'extracted' in pobj:
                        val = pobj.get('extracted')
                    elif isinstance(pobj, dict) and 'from' in pobj and isinstance(pobj.get('from'), dict):
                        val = pobj['from'].get('extracted')
                    if val is not None and isinstance(val, (int, float)) and 0.25 < val < 5000:
                        out.append(float(val))
                if include_debug and out:
                    debug_log.append(f"serpapi: {len(out)} prices")
                return out
            except Exception as e:
                if include_debug:
                    debug_log.append(f"serpapi: {type(e).__name__}")
                return []
        
        prices = []
        if _SERPAPI_KEY:
            prices = _fetch_serpapi(query)
        if len(prices) < 2:
            q_enc = requests.utils.quote(query)
            url1 = f"https://www.ebay.com/sch/i.html?_nkw={q_enc}&_sacat=261328&LH_Sold=1&LH_Complete=1"
            url2 = f"https://www.ebay.com/sch/i.html?_nkw={q_enc}&LH_Sold=1&LH_Complete=1"
            prices = _fetch_ebay(url1, "url1")
            if len(prices) < 2:
                prices = _fetch_ebay(url2, "url2")
            if len(prices) < 2 and self._cloud:
                prices = _fetch_ebay(url1, "url1", use_cloud=True)
        if len(prices) < 2 and set_short:
            fallback = f"{player_name} basketball card"
            if card_number and str(card_number).strip():
                fallback += f" #{card_number}"
            if _SERPAPI_KEY:
                prices = _fetch_serpapi(fallback)
            if len(prices) < 2:
                prices = _fetch_ebay(f"https://www.ebay.com/sch/i.html?_nkw={requests.utils.quote(fallback)}&_sacat=261328&LH_Sold=1&LH_Complete=1", "fallback")
            if len(prices) < 2 and self._cloud:
                prices = _fetch_ebay(f"https://www.ebay.com/sch/i.html?_nkw={requests.utils.quote(fallback)}&_sacat=261328&LH_Sold=1&LH_Complete=1", "fallback", use_cloud=True)
        
        if prices:
            prices = list(dict.fromkeys(p for p in prices if 0.25 < p < 2000))
            if prices:
                prices.sort()
                prices = prices[:10]
                result['min'] = round(min(prices), 2)
                result['max'] = round(max(prices), 2)
                result['avg'] = round(sum(prices) / len(prices), 2)
                result['median'] = round(prices[len(prices) // 2], 2)
                result['last_sold'] = round(prices[0], 2)
                result['suggested'] = result['median']
                result['count'] = len(prices)
                result['samples'] = [{'price': round(p, 2), 'title': ''} for p in prices[:5]]
        elif include_debug and debug_log:
            result['_debug'] = ' | '.join(debug_log)
        
        return result
    
    def _empty(self) -> Dict:
        return {'min': None, 'max': None, 'avg': None, 'median': None, 'last_sold': None, 'suggested': None, 'count': 0, 'samples': []}
    
    def suggest_price(self, player_name: str, set_name: str, card_number: Optional[str] = None, parallel_type: Optional[str] = None, strategy: str = 'median') -> Optional[float]:
        data = self.get_ebay_sold_prices(player_name, set_name, card_number, parallel_type)
        return data.get(strategy) or data.get('suggested') or data.get('median') or data.get('avg') or data.get('min')
