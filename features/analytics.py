"""Analytics dashboard - sales metrics, best sellers, revenue."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class AnalyticsDashboard:
    """Aggregate and display seller analytics."""
    
    def __init__(self, api_client=None, payments_data: Optional[List] = None):
        self.api_client = api_client
        self.payments_data = payments_data or []
    
    def get_sales_summary(
        self,
        days: int = 30,
        user_email: Optional[str] = None
    ) -> Dict:
        """
        Return summary: total_sales, count, avg_sale, top_sets, recent_activity.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        sales = []
        for p in self.payments_data:
            if isinstance(p, dict):
                date_str = p.get('date') or p.get('created_at')
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except Exception:
                        continue
                    if dt.replace(tzinfo=None) >= cutoff.replace(tzinfo=None):
                        amt = float(p.get('amount', 0) or p.get('amount_paid', 0))
                        sales.append({'date': date_str, 'amount': amt, 'title': p.get('title', '')})
        
        total = sum(s['amount'] for s in sales)
        count = len(sales)
        
        return {
            'total_sales': round(total, 2),
            'transaction_count': count,
            'avg_sale': round(total / count, 2) if count else 0,
            'period_days': days,
            'recent': sales[-10:] if sales else []
        }
    
    def get_listing_stats(self, token: Optional[str] = None) -> Dict:
        """Get listing counts: active, draft, unsold, total."""
        if not self.api_client:
            return {'active': 0, 'draft': 0, 'unsold': 0, 'total': 0}
        try:
            # Would call eBay API for listing counts
            return {'active': 0, 'draft': 0, 'unsold': 0, 'total': 0}
        except Exception:
            return {'active': 0, 'draft': 0, 'unsold': 0, 'total': 0}
    
    def get_best_sellers(self, limit: int = 10) -> List[Dict]:
        """From payments/order data, aggregate by title/set."""
        by_title = {}
        for p in self.payments_data:
            if isinstance(p, dict):
                t = p.get('title') or p.get('set_name') or 'Unknown'
                amt = float(p.get('amount', 0) or p.get('amount_paid', 0))
                by_title[t] = by_title.get(t, 0) + amt
        sorted_items = sorted(by_title.items(), key=lambda x: -x[1])[:limit]
        return [{'title': t, 'revenue': round(r, 2)} for t, r in sorted_items]
