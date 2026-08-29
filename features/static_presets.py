"""Load bundled checklist presets from presets/*.json."""
import json
import os
import re
from typing import Dict, List, Optional


PRESETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'presets')


def _normalize_url(url: str) -> str:
    return (url or '').strip().lower().rstrip('/')


def list_static_presets() -> List[Dict]:
    presets = []
    if not os.path.isdir(PRESETS_DIR):
        return presets
    for name in sorted(os.listdir(PRESETS_DIR)):
        if not name.endswith('.json'):
            continue
        path = os.path.join(PRESETS_DIR, name)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data['_file'] = name
            presets.append(data)
        except Exception as e:
            print(f"[PRESETS] Failed to load {name}: {e}")
    return presets


def find_matching_preset(url: str, checklist_type: str = 'base') -> Optional[Dict]:
    """Find a bundled preset matching URL and checklist type."""
    norm_url = _normalize_url(url)
    ctype = (checklist_type or 'base').lower()
    # Aliases so UI "Prospects" matches prospects presets
    if ctype in ('bp', 'base_prospects', 'base-prospects'):
        ctype = 'prospects'
    for preset in list_static_presets():
        preset_url = _normalize_url(preset.get('url') or preset.get('beckettUrl') or '')
        preset_type = (preset.get('type') or 'base').lower()
        if preset_type != ctype:
            continue
        if preset_url and (norm_url == preset_url or norm_url.endswith(preset_url.split('/')[-1])):
            return preset
        match_urls = preset.get('matchUrls') or []
        for mu in match_urls:
            if _normalize_url(mu) in norm_url or norm_url in _normalize_url(mu):
                return preset
    return None


def filter_cards_by_preset(cards: List[Dict], flt: Dict) -> List[Dict]:
    """Filter cards per preset rules (e.g. plain 1-100 only, or BP- only)."""
    if not flt:
        return cards
    max_num = flt.get('maxNumber')
    min_num = flt.get('minNumber', 1)
    exclude_prefixes = flt.get('excludePrefixes') or []
    include_prefixes = flt.get('includePrefixes') or []
    plain_only = flt.get('plainNumbersOnly', False)
    exclude_plain = flt.get('excludePlainNumbers', False)
    result = []
    for card in cards:
        num = str(card.get('number', '')).strip()
        if not num:
            continue
        if exclude_plain and num.isdigit():
            continue
        if plain_only and not num.isdigit():
            continue
        if include_prefixes and not any(num.startswith(p) for p in include_prefixes):
            continue
        excluded = False
        for prefix in exclude_prefixes:
            if num.startswith(prefix):
                excluded = True
                break
        if excluded:
            continue
        if num.isdigit():
            n = int(num)
            if n < min_num:
                continue
            if max_num is not None and n > max_num:
                continue
        result.append(card)
    return result


def merge_preset_into_cards(cards: List[Dict], preset_cards: List[Dict]) -> List[Dict]:
    """Apply preset metadata by card number; only overwrite price/qty when present on preset."""
    if not preset_cards:
        return cards
    by_num = {}
    for pc in preset_cards:
        num = str(pc.get('number', '')).strip()
        if num:
            by_num[num] = pc
    existing_nums = set()
    for card in cards:
        num = str(card.get('number', '')).strip()
        existing_nums.add(num)
        pc = by_num.get(num)
        if not pc:
            continue
        if 'price' in pc and pc['price'] is not None:
            card['price'] = float(pc['price'])
        if 'quantity' in pc and pc['quantity'] is not None:
            card['quantity'] = int(pc['quantity'])
        elif 'qty' in pc and pc['qty'] is not None:
            card['quantity'] = int(pc['qty'])
        if pc.get('team'):
            card['team'] = pc['team']
        if pc.get('name') and not card.get('name'):
            card['name'] = pc['name']
    for num, pc in by_num.items():
        if num in existing_nums:
            continue
        entry = {
            'number': num,
            'name': pc.get('name', ''),
            'team': pc.get('team', ''),
            'imageUrl': pc.get('imageUrl', pc.get('image_url', '')),
        }
        if 'price' in pc and pc['price'] is not None:
            entry['price'] = float(pc['price'])
        else:
            entry['price'] = float(cards[0].get('price', 1.0)) if cards else 1.0
        if 'quantity' in pc and pc['quantity'] is not None:
            entry['quantity'] = int(pc['quantity'])
        elif 'qty' in pc and pc['qty'] is not None:
            entry['quantity'] = int(pc['qty'])
        else:
            entry['quantity'] = int(cards[0].get('quantity', 0)) if cards else 0
        cards.append(entry)
    if cards and all(str(c.get('number', '')).isdigit() for c in cards):
        cards.sort(key=lambda c: int(c['number']))
    return cards
