"""Staggered publishing - schedule listings to go live over time."""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable


class StaggeredPublisher:
    """Publish listings with delays between each to avoid rate limits and stagger visibility."""
    
    def __init__(
        self,
        delay_minutes: int = 30,
        max_per_hour: int = 20,
        publish_fn: Optional[Callable] = None
    ):
        self.delay_minutes = delay_minutes
        self.max_per_hour = max_per_hour
        self.publish_fn = publish_fn
    
    def compute_schedule(
        self,
        count: int,
        start_offset_hours: int = 1
    ) -> List[datetime]:
        """
        Compute publish times for `count` listings.
        Returns list of datetime objects for when each should publish.
        """
        base = datetime.utcnow() + timedelta(hours=start_offset_hours)
        times = []
        delay = timedelta(minutes=self.delay_minutes)
        for i in range(count):
            times.append(base + i * delay)
        return times
    
    def run_staggered(
        self,
        items: List[Dict],
        create_listing_fn: Callable,
        start_offset_hours: int = 1,
        on_progress: Optional[Callable[[int, int, Dict], None]] = None
    ) -> List[Dict]:
        """
        Create listings one by one with delay between each.
        items: list of listing payloads
        create_listing_fn: fn(item) -> result dict
        Returns list of results.
        """
        results = []
        delay_secs = self.delay_minutes * 60
        
        for i, item in enumerate(items):
            try:
                r = create_listing_fn(item)
                results.append(r)
                if on_progress:
                    on_progress(i + 1, len(items), r)
            except Exception as e:
                results.append({'error': str(e), 'item': item})
            
            if i < len(items) - 1:
                time.sleep(delay_secs)
        
        return results
