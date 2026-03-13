"""Saved checklist presets - URL, type, filters."""
import json
import os
from typing import Dict, List, Optional


PRESETS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'checklist_presets.json')


class PresetManager:
    """Manage saved checklist presets per user."""
    
    def __init__(self, user_email: Optional[str] = None):
        self.user_email = user_email or 'default'
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        d = os.path.dirname(PRESETS_FILE)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
    
    def _load_all(self) -> Dict:
        if os.path.exists(PRESETS_FILE):
            try:
                with open(PRESETS_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_all(self, data: Dict):
        self._ensure_data_dir()
        with open(PRESETS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_presets(self) -> List[Dict]:
        data = self._load_all()
        user = data.get(self.user_email, [])
        return user
    
    def save_preset(self, name: str, url: str, checklist_type: str = 'base', filters: Optional[Dict] = None):
        data = self._load_all()
        if self.user_email not in data:
            data[self.user_email] = []
        presets = data[self.user_email]
        preset = {'name': name, 'url': url, 'type': checklist_type, 'filters': filters or {}}
        # Replace if same name
        presets = [p for p in presets if p.get('name') != name]
        presets.append(preset)
        data[self.user_email] = presets
        self._save_all(data)
    
    def load_preset(self, name: str) -> Optional[Dict]:
        for p in self.list_presets():
            if p.get('name') == name:
                return p
        return None
    
    def delete_preset(self, name: str):
        data = self._load_all()
        if self.user_email in data:
            data[self.user_email] = [p for p in data[self.user_email] if p.get('name') != name]
            self._save_all(data)
