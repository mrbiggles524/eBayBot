"""
Migrate listings from Sandbox to Production.
⚠️ WARNING: This requires explicit confirmation and will publish to LIVE eBay.
"""
import sys
import os
from ebay_api_client import eBayAPIClient
from config import Config
import json

# PRODUCTION MIGRATION IS DISABLED BY DEFAULT
PRODUCTION_MIGRATION_ENABLED = False

def check_production_ready():
    """Check if we're ready for production migration."""
    print("=" * 80)
    print("PRODUCTION MIGRATION CHECK")
    print("=" * 80)
    print()
    
    # Check environment
    config = Config()
    if config.EBAY_ENVIRONMENT != 'sandbox':
        print("[ERROR] You must be in SANDBOX environment to migrate to production")
        return False
    
    # Check for production token
    if not config.EBAY_PRODUCTION_TOKEN:
        print("[ERROR] EBAY_PRODUCTION_TOKEN not set in .env")
        print("You need a production token to migrate to production")
        return False
    
    # Check policies
    if not config.RETURN_POLICY_ID or not config.FULFILLMENT_POLICY_ID or not config.PAYMENT_POLICY_ID:
        print("[WARNING] Some policies are not set")
        print("Make sure all policies exist in production")
    
    print("[OK] Basic checks passed")
    print()
    return True

def migrate_to_production(sku: str, confirm: bool = False):
    """Migrate a listing from sandbox to production."""
    print("=" * 80)
    print("⚠️  PRODUCTION MIGRATION")
    print("=" * 80)
    print()
    
    if not PRODUCTION_MIGRATION_ENABLED:
        print("[ERROR] Production migration is DISABLED")
        print()
        print("To enable production migration:")
        print("1. Edit migrate_to_production.py")
        print("2. Set PRODUCTION_MIGRATION_ENABLED = True")
        print("3. Run this script again with --confirm flag")
        print()
        print("⚠️  WARNING: This will publish to LIVE eBay!")
        return
    
    if not confirm:
        print("[ERROR] Production migration requires explicit confirmation")
        print()
        print("Usage: python migrate_to_production.py <SKU> --confirm")
        print()
        print("⚠️  WARNING: This will:")
        print("  1. Copy listing from sandbox to production")
        print("  2. Publish it to LIVE eBay")
        print("  3. Make it visible to real buyers")
        return
    
    if not check_production_ready():
        return
    
    print(f"Migrating SKU: {sku}")
    print()
    print("⚠️  FINAL WARNING: This will publish to PRODUCTION eBay!")
    print()
    
    response = input("Type 'MIGRATE TO PRODUCTION' to confirm: ")
    if response != 'MIGRATE TO PRODUCTION':
        print("[CANCELLED] Migration cancelled")
        return
    
    config = Config()
    
    # Get sandbox listing
    print("Fetching sandbox listing...")
    sandbox_client = eBayAPIClient()  # Uses sandbox by default
    
    offer_result = sandbox_client.get_offer_by_sku(sku)
    if not offer_result.get('success') or not offer_result.get('offer'):
        print(f"[ERROR] Could not get sandbox offer for SKU {sku}")
        return
    
    sandbox_offer = offer_result['offer']
    print("[OK] Sandbox listing fetched")
    print()
    
    # Switch to production
    print("Switching to production environment...")
    # Note: This would require switching the config
    # For now, we'll just show what would happen
    
    print()
    print("[INFO] Production migration would:")
    print("  1. Copy listing data from sandbox")
    print("  2. Create inventory item in production")
    print("  3. Create offer in production")
    print("  4. Publish to production")
    print()
    print("⚠️  This feature requires:")
    print("  - Production API credentials")
    print("  - Production policies")
    print("  - Explicit confirmation")
    print()
    print("For now, please manually recreate the listing in production using the Streamlit UI")
    print("with production environment selected.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_production.py <SKU> [--confirm]")
        print()
        print("⚠️  WARNING: Production migration is DISABLED by default")
        print("Edit this file and set PRODUCTION_MIGRATION_ENABLED = True to enable")
        sys.exit(1)
    
    sku = sys.argv[1]
    confirm = '--confirm' in sys.argv
    
    migrate_to_production(sku, confirm)
