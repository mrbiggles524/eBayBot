"""Server-side checklist drafts: price/qty keyed by user email + checklist id."""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional


DRAFTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'checklist_drafts.json')


def checklist_id_from_url(url: str, checklist_type: str = 'base') -> str:
    """Stable id for a checklist URL + type."""
    url = (url or '').strip().lower().rstrip('/')
    slug = url.split('/')[-1] if url else 'unknown'
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-') or 'unknown'
    return f"{slug}:{checklist_type or 'base'}"


class ChecklistDraftManager:
    """Persist price/qty edits per user and checklist."""

    def __init__(self, user_email: Optional[str] = None):
        self.user_email = (user_email or 'default').strip().lower()
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        d = os.path.dirname(DRAFTS_FILE)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

    def _load_all(self) -> Dict:
        if os.path.exists(DRAFTS_FILE):
            try:
                with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_all(self, data: Dict):
        self._ensure_data_dir()
        with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def save_draft(
        self,
        checklist_id: str,
        cards: List[Dict],
        meta: Optional[Dict] = None,
    ):
        data = self._load_all()
        if self.user_email not in data:
            data[self.user_email] = {}
        entries = []
        for c in cards or []:
            num = str(c.get('number', '')).strip()
            if not num:
                continue
            entries.append({
                'number': num,
                'price': float(c.get('price', 1) or 0),
                'quantity': int(c.get('quantity', c.get('qty', 0)) or 0),
                'name': c.get('name', ''),
                'team': c.get('team', ''),
            })
        data[self.user_email][checklist_id] = {
            'checklist_id': checklist_id,
            'updated': datetime.utcnow().isoformat() + 'Z',
            'cards': entries,
            'meta': meta or {},
        }
        self._save_all(data)

    def load_draft(self, checklist_id: str) -> Optional[Dict]:
        data = self._load_all()
        return (data.get(self.user_email) or {}).get(checklist_id)

    def delete_draft(self, checklist_id: str):
        data = self._load_all()
        if self.user_email in data and checklist_id in data[self.user_email]:
            del data[self.user_email][checklist_id]
            self._save_all(data)


def merge_draft_into_cards(cards: List[Dict], draft_entries: List[Dict]) -> List[Dict]:
    """Merge saved price/qty onto fetched cards by card number."""
    if not draft_entries:
        return cards
    by_num = {str(d.get('number', '')).strip(): d for d in draft_entries if d.get('number') is not None}
    for card in cards:
        num = str(card.get('number', '')).strip()
        saved = by_num.get(num)
        if not saved:
            continue
        if 'price' in saved:
            card['price'] = float(saved['price'])
        if 'quantity' in saved:
            card['quantity'] = int(saved['quantity'])
    return cards

def clear_stale_bowman_base_drafts_once():
    """One-time: drop finished-listing prices for 2026 Bowman base drafts."""
    flag_key = '__cleared_bowman_base_v4162__'
    checklist_id = '2026-bowman-baseball-cards:base'
    if not os.path.exists(DRAFTS_FILE):
        return
    try:
        with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return
    if data.get(flag_key):
        return
    cleared = 0
    for user, drafts in list(data.items()):
        if not isinstance(drafts, dict) or user.startswith('__'):
            continue
        if checklist_id in drafts:
            del drafts[checklist_id]
            cleared += 1
    data[flag_key] = True
    try:
        with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f'[DRAFTS] Cleared stale Bowman base drafts for {cleared} user(s)')
    except Exception as e:
        print(f'[DRAFTS] Failed to clear stale drafts: {e}')

