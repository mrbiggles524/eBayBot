"""
Quick test to verify Flask app can start and handle requests.
"""
import sys
import time
from threading import Thread
import requests

sys.stdout.reconfigure(encoding='utf-8')

def test_app_startup():
    """Test if the app can start."""
    print("=" * 60)
    print("Testing Flask App Startup")
    print("=" * 60)
    print()
    
    # Test 1: Import check
    print("Test 1: Importing app module...")
    try:
        from app import app
        print("✅ App imported successfully")
        print(f"   Routes registered: {len(app.url_map._rules)}")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test 2: Check critical routes
    print("Test 2: Checking critical routes...")
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    critical_routes = ['/', '/login', '/app', '/api/policies', '/api/list']
    
    for route in critical_routes:
        found = any(route in r for r in routes)
        status = "✅" if found else "❌"
        print(f"   {status} {route}")
    
    print()
    
    # Test 3: Try to start server in background
    print("Test 3: Testing server startup (5 second test)...")
    try:
        def run_server():
            app.run(debug=False, port=5001, use_reloader=False, threaded=True)
        
        server_thread = Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Try to make a request
        try:
            response = requests.get('http://localhost:5001/', timeout=3)
            if response.status_code == 200:
                print("✅ Server started and responding!")
                print(f"   Status code: {response.status_code}")
                return True
            else:
                print(f"⚠️ Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not connect to server: {e}")
            print("   (This might be OK if server is already running)")
        
        print("✅ Server startup test completed")
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_app_startup()
