"""Main eBay posting bot for card listings."""
import argparse
from typing import List, Dict, Optional, Union
from card_checklist import CardChecklistFetcher
from ebay_listing import eBayListingManager
from config import Config
from ebay_oauth import eBayOAuth
from ebay_setup import eBayAutoSetup

class eBayCardBot:
    """Main bot for posting card listings to eBay."""
    
    def __init__(self):
        self.config = Config()
        self.checklist_fetcher = CardChecklistFetcher()
        self.listing_manager = eBayListingManager()
    
    def list_cards_from_set(
        self,
        set_name: Optional[str] = None,
        csv_file: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        price: Union[float, Dict[str, float]] = 0.99,
        quantity: int = 1,
        condition: Optional[str] = None,
        category: str = "Trading Cards",
        filter_cards: Optional[List[str]] = None,
        publish: bool = True
    ) -> Dict:
        """
        List multiple cards from a set as variations.
        
        Args:
            set_name: Name of the card set (if not using CSV)
            csv_file: Path to CSV file with card data
            title: Custom listing title (defaults to set name)
            description: Custom description
            price: Price per card (float) or dict mapping card name/number to price
            quantity: Quantity per card
            condition: Card condition
            category: eBay category
            filter_cards: Optional list of card names/numbers to include only
            publish: Whether to publish the listing immediately
            
        Returns:
            Dictionary with listing results
        """
        if csv_file:
            print(f"Loading cards from CSV file: {csv_file}")
            cards = self.checklist_fetcher.get_set_checklist(csv_file=csv_file)
        else:
            if not set_name:
                return {"success": False, "error": "Either set_name or csv_file must be provided"}
            print(f"Fetching checklist for set: {set_name}")
            cards = self.checklist_fetcher.get_set_checklist(set_name)
        
        if not cards:
            return {
                "success": False,
                "error": f"No cards found for set: {set_name}"
            }
        
        print(f"Found {len(cards)} cards in set")
        
        # Filter cards if specified
        if filter_cards:
            filtered = []
            for card in cards:
                if any(f.lower() in card.get('name', '').lower() or 
                       f.lower() in card.get('number', '').lower() 
                       for f in filter_cards):
                    filtered.append(card)
            cards = filtered
            print(f"Filtered to {len(cards)} cards")
        
        if not cards:
            return {
                "success": False,
                "error": "No cards match the filter criteria"
            }
        
        # Generate title and description if not provided
        if not title:
            set_display_name = cards[0].get('set_name', set_name or 'Card Set') if cards else 'Card Set'
            title = f"{set_display_name} - Complete Set ({len(cards)} Cards)"
        
        if not description:
            set_display_name = cards[0].get('set_name', set_name or 'Card Set') if cards else 'Card Set'
            description = self._generate_description(cards, set_display_name)
        
        # Get category ID
        category_id = self.listing_manager.get_category_id(category)
        
        # Handle per-card pricing from CSV
        if isinstance(price, dict) or any(card.get('price') for card in cards):
            pricing_dict = {}
            if isinstance(price, dict):
                pricing_dict = price
            else:
                # Build pricing dict from cards
                for card in cards:
                    card_price = card.get('price')
                    if card_price:
                        card_name = card.get('name', '')
                        card_number = card.get('number', '')
                        if card_name:
                            pricing_dict[card_name] = float(card_price)
                        if card_number:
                            pricing_dict[card_number] = float(card_price)
            price = pricing_dict if pricing_dict else price
        
        # Create listing
        print(f"Creating eBay listing: {title}")
        result = self.listing_manager.create_variation_listing(
            cards=cards,
            title=title,
            description=description,
            category_id=category_id,
            price=price,
            quantity=quantity,
            condition=condition or self.config.DEFAULT_CONDITION,
            publish=publish
        )
        
        return result
    
    def _generate_description(self, cards: List[Dict], set_name: str) -> str:
        """Generate a description for the listing."""
        description = f"<h2>{set_name} - Complete Card Set</h2>\n"
        description += f"<p>This listing includes {len(cards)} cards from the {set_name} set.</p>\n"
        description += "<h3>Cards Included:</h3>\n<ul>\n"
        
        for card in cards[:50]:  # Limit to first 50 for description length
            card_name = card.get('name', 'Unknown')
            card_number = card.get('number', '')
            description += f"<li>{card_name} #{card_number}</li>\n"
        
        if len(cards) > 50:
            description += f"<li>... and {len(cards) - 50} more cards</li>\n"
        
        description += "</ul>\n"
        description += "<p>All cards are listed as variations. Select your desired card from the dropdown menu.</p>"
        
        return description
    
    def search_sets(self, query: str) -> List[Dict]:
        """Search for card sets."""
        return self.checklist_fetcher.search_set(query)

def main():
    """Main entry point for the bot."""
    parser = argparse.ArgumentParser(description='eBay Card Listing Bot')
    parser.add_argument('set_name', nargs='?', help='Name of the card set to list')
    parser.add_argument('--csv', '--csv-file', dest='csv_file', help='Path to CSV file with card data')
    parser.add_argument('--title', help='Custom listing title')
    parser.add_argument('--description', help='Custom listing description')
    parser.add_argument('--price', type=float, default=0.99, help='Price per card (or use price column in CSV)')
    parser.add_argument('--quantity', type=int, default=1, help='Quantity per card')
    parser.add_argument('--condition', help='Card condition (New, Used, etc.)')
    parser.add_argument('--category', default='Trading Cards', help='eBay category')
    parser.add_argument('--filter', nargs='+', help='Filter cards by name/number')
    parser.add_argument('--search', action='store_true', help='Search for sets instead of listing')
    parser.add_argument('--no-publish', action='store_true', help='Create listing but do not publish')
    parser.add_argument('--login', action='store_true', help='Login using OAuth')
    parser.add_argument('--logout', action='store_true', help='Logout and remove saved token')
    parser.add_argument('--refresh-token', action='store_true', help='Refresh OAuth token')
    parser.add_argument('--setup', action='store_true', help='Auto-setup from eBay user ID (fetches all required info)')
    parser.add_argument('--user-id', help='eBay user ID for setup (optional, will use current user if not provided)')
    parser.add_argument('--verify', action='store_true', help='Verify current setup configuration')
    
    args = parser.parse_args()
    
    # Handle login/logout commands
    if args.login:
        oauth = eBayOAuth()
        result = oauth.login()
        if result.get('success'):
            print(f"\n✓ Login successful!")
            print(f"  Access token expires in: {result.get('expires_in', 0)} seconds")
        else:
            print(f"\n✗ Login failed: {result.get('error')}")
        return
    
    if args.logout:
        oauth = eBayOAuth()
        oauth.logout()
        return
    
    if args.refresh_token:
        oauth = eBayOAuth()
        result = oauth.refresh_token()
        if result.get('success'):
            print(f"\n✓ Token refreshed successfully!")
            print(f"  New token expires in: {result.get('expires_in', 0)} seconds")
        else:
            print(f"\n✗ Token refresh failed: {result.get('error')}")
        return
    
    if args.setup:
        setup = eBayAutoSetup()
        result = setup.setup_from_user_id(args.user_id)
        if result.get('success'):
            print(f"\n✓ Setup completed successfully!")
            setup_info = result.get('setup_info', {})
            if setup_info.get('config_saved', {}).get('success'):
                print(f"  Configuration saved to .env")
        else:
            print(f"\n✗ Setup failed: {result.get('error')}")
        return
    
    if args.verify:
        setup = eBayAutoSetup()
        result = setup.verify_setup()
        if result.get('success'):
            print(f"\n✓ {result.get('message')}")
        else:
            print(f"\n✗ Setup verification failed:")
            for issue in result.get('issues', []):
                print(f"  - {issue}")
        return
    
    bot = eBayCardBot()
    
    if args.search:
        if not args.set_name:
            print("Error: set_name required for search")
            return
        results = bot.search_sets(args.set_name)
        print(f"Found {len(results)} sets matching '{args.set_name}':")
        for result in results:
            print(f"  - {result.get('name', 'Unknown')}")
    else:
        if not args.set_name and not args.csv_file:
            parser.error("Either set_name or --csv must be provided")
        
        result = bot.list_cards_from_set(
            set_name=args.set_name,
            csv_file=args.csv_file,
            title=args.title,
            description=args.description,
            price=args.price,
            quantity=args.quantity,
            condition=args.condition,
            category=args.category,
            filter_cards=args.filter,
            publish=not args.no_publish
        )
        
        if result.get('success'):
            print(f"\n✓ Listing created successfully!")
            print(f"  Offer ID: {result.get('offerId')}")
            if result.get('listingId'):
                print(f"  Listing ID: {result.get('listingId')}")
            print(f"  Items Created: {result.get('itemsCreated', 0)}")
            if result.get('warnings'):
                print(f"  Warnings: {result.get('warnings')}")
        else:
            print(f"\n✗ Error creating listing: {result.get('error')}")
            if result.get('errors'):
                print("  Additional errors:")
                for err in result.get('errors', []):
                    print(f"    - {err}")

if __name__ == "__main__":
    main()
