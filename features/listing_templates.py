"""Listing templates - save and reuse title, description, images."""
import json
import os
from typing import Dict, List, Optional


TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'listing_templates.json')


class ListingTemplateManager:
    """Manage saved listing templates per user."""
    
    def __init__(self, user_email: Optional[str] = None):
        self.user_email = user_email or 'default'
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        d = os.path.dirname(TEMPLATES_FILE)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
    
    def _load_all(self) -> Dict:
        if os.path.exists(TEMPLATES_FILE):
            try:
                with open(TEMPLATES_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_all(self, data: Dict):
        self._ensure_data_dir()
        with open(TEMPLATES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_templates(self) -> List[Dict]:
        data = self._load_all()
        return data.get(self.user_email, [])
    
    def save_template(
        self,
        name: str,
        title_template: str,
        description: str,
        default_price: float = 1.00,
        images: Optional[List[str]] = None,
        meta: Optional[Dict] = None
    ):
        data = self._load_all()
        if self.user_email not in data:
            data[self.user_email] = []
        templates = data[self.user_email]
        t = {
            'name': name,
            'title_template': title_template,
            'description': description,
            'default_price': default_price,
            'images': images or [],
            'meta': meta or {}
        }
        templates = [x for x in templates if x.get('name') != name]
        templates.append(t)
        data[self.user_email] = templates
        self._save_all(data)
    
    def load_template(self, name: str) -> Optional[Dict]:
        for t in self.list_templates():
            if t.get('name') == name:
                return t
        return None
    
    def delete_template(self, name: str):
        data = self._load_all()
        if self.user_email in data:
            data[self.user_email] = [t for t in data[self.user_email] if t.get('name') != name]
            self._save_all(data)
