"""
Automated script to create listings in production as drafts.
This bypasses sandbox limitations and creates real drafts you can view.
"""
import sys
from pathlib import Path
from ebay_listing import eBayListingManager
from config import Config
import json

def create_production_drafts():
    """Create listings in production as drafts automatically."""
    print("=" * 80)
    print("Creating Production Drafts (Automated)")
    print("=" * 80)
    print()
    
    # Check environment
    config = Config()
    if config.EBAY_ENVIRONMENT.lower() != 'production':
        print("⚠️  WARNING: Not in production environment!")
        print(f"   Current environment: {config.EBAY_ENVIRONMENT}")
        print()
        print("To switch to production, run:")
        print("   python switch_to_production.py")
        print()
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            return
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Check if we have a Beckett URL or need to use existing cards
    if len(sys.argv) > 1:
        beckett_url = sys.argv[1]
        print(f"Beckett URL: {beckett_url}")
        print()
        print("This script will:")
        print("  1. Fetch cards from Beckett URL")
        print("  2. Create listings as DRAFTS (not published)")
        print("  3. Save them to your production eBay account")
        print()
        print("⚠️  IMPORTANT: These will be REAL drafts in your production account!")
        print("   They will NOT be published/live, but you can view them in Seller Hub.")
        print()
        
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Import the bot to fetch cards
        try:
            from ebay_bot import eBayCardBot
            bot = eBayCardBot()
            
            print("Fetching cards from Beckett...")
            cards = bot.fetch_cards_from_beckett(beckett_url)
            
            if not cards:
                print("[ERROR] No cards found!")
                return
            
            print(f"Found {len(cards)} cards")
            print()
            
            # Create listing manager
            listing_manager = eBayListingManager()
            
            # Create variation listing as draft
            print("Creating variation listing as DRAFT...")
            result = listing_manager.create_variation_listing(
                cards=cards,
                title="Trading Cards - Draft Listing",
                description="This is a draft listing created automatically. All cards are in excellent condition.",
                category_id="261328",
                price=1.0,
                quantity=1,
                condition="Near Mint",
                publish=False  # CRITICAL: Create as draft, not published
            )
            
            if result.get('success'):
                print()
                print("=" * 80)
                print("✅ SUCCESS! Draft Listing Created")
                print("=" * 80)
                print()
                print("Your listing has been created as a DRAFT in production.")
                print("You can:")
                print("  1. View it in eBay Seller Hub (My eBay > Selling > Drafts)")
                print("  2. Add images to it")
                print("  3. Edit details")
                print("  4. Publish when ready")
                print()
            else:
                error = result.get('error', 'Unknown error')
                print()
                print("=" * 80)
                print("❌ Failed to Create Draft")
                print("=" * 80)
                print(f"Error: {error}")
                print()
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Usage: python create_production_drafts.py <beckett_url>")
        print()
        print("Example:")
        print("  python create_production_drafts.py https://www.beckett.com/news/...")
        print()
        print("Or use the Streamlit UI:")
        print("  1. Run: python switch_to_production.py")
        print("  2. Run: python -m streamlit run start.py")
        print("  3. Go to Step 5 and create listings (they'll be drafts)")

if __name__ == "__main__":
    create_production_drafts()
