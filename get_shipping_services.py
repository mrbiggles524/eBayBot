"""
Query eBay's metadata API to get valid shipping service codes.
This will help us find the exact code for eBay Standard Envelope.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Get Valid Shipping Service Codes")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try to get shipping services from metadata API
    print("Querying eBay Metadata API for shipping services...")
    print()
    
    try:
        # Metadata API endpoint for shipping services
        endpoint = "/sell/metadata/v1/marketplace/EBAY_US/get_shipping_services"
        response = client._make_request('GET', endpoint)
        
        if response.status_code == 200:
            data = response.json()
            services = data.get('shippingServices', [])
            
            print(f"[OK] Found {len(services)} shipping service(s)")
            print()
            
            # Look for eBay Standard Envelope
            print("Searching for eBay Standard Envelope...")
            print()
            
            envelope_services = []
            for service in services:
                service_code = service.get('shippingServiceCode', '')
                service_name = service.get('shippingServiceName', '')
                carrier = service.get('shippingCarrierCode', '')
                
                # Check if it's related to Standard Envelope
                if 'envelope' in service_name.lower() or 'standard' in service_name.lower() or 'eBay' in service_name:
                    envelope_services.append({
                        'code': service_code,
                        'name': service_name,
                        'carrier': carrier
                    })
            
            if envelope_services:
                print("[OK] Found eBay Standard Envelope service(s):")
                for svc in envelope_services:
                    print(f"  Service Code: {svc['code']}")
                    print(f"  Service Name: {svc['name']}")
                    print(f"  Carrier: {svc['carrier']}")
                    print()
            else:
                print("[WARNING] eBay Standard Envelope not found in available services")
                print()
                print("Available USPS services (first 20):")
                usps_services = [s for s in services if s.get('shippingCarrierCode') == 'USPS'][:20]
                for svc in usps_services:
                    code = svc.get('shippingServiceCode', 'N/A')
                    name = svc.get('shippingServiceName', 'N/A')
                    print(f"  {code}: {name}")
            
            # Save full list to file for reference
            with open('shipping_services_list.json', 'w') as f:
                json.dump(data, f, indent=2)
            print()
            print("[INFO] Full service list saved to: shipping_services_list.json")
            
        else:
            print(f"[ERROR] Status {response.status_code}")
            print(response.text[:1000])
            print()
            print("The metadata API might not be available in sandbox.")
            print("eBay Standard Envelope might only be available in production.")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Note: The metadata API might not be available in sandbox.")
        print("eBay Standard Envelope is likely only available in production environment.")

if __name__ == "__main__":
    main()
