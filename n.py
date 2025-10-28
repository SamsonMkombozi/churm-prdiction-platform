"""
CRM API Debug Script
debug_crm_api.py

Run this script to test your CRM API directly and see what's happening
"""
import requests
import json

def test_crm_api(base_url, table_name='crm_customers'):
    """Test CRM API and provide detailed debugging information"""
    print(f"🔍 Testing CRM API: {base_url}")
    print(f"📊 Table: {table_name}")
    print("=" * 60)
    
    # Build URL
    test_url = f"{base_url}?table={table_name}&limit=1"
    print(f"🔗 Full URL: {test_url}")
    print()
    
    try:
        print("🚀 Making request...")
        response = requests.get(test_url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        print()
        
        print(f"📊 Content Length: {len(response.content)} bytes")
        print(f"📊 Content Type: {response.headers.get('content-type', 'Unknown')}")
        print()
        
        # Check if response is empty
        if len(response.content) == 0:
            print("❌ PROBLEM: Empty response!")
            print("   - Check if the API URL is correct")
            print("   - Check if the server is running")
            print("   - Check if the table name is correct")
            return False
        
        # Show response preview
        response_text = response.text
        print(f"📄 Response Preview (first 500 chars):")
        print("-" * 40)
        print(response_text[:500])
        if len(response_text) > 500:
            print("... (truncated)")
        print("-" * 40)
        print()
        
        # Check if it looks like HTML
        if response_text.strip().startswith('<!DOCTYPE') or response_text.strip().startswith('<html'):
            print("❌ PROBLEM: Received HTML instead of JSON!")
            print("   - This usually means the endpoint is wrong")
            print("   - Or the server has an error")
            print("   - Check the API documentation")
            return False
        
        # Check if it looks like an error page
        if 'error' in response_text.lower() and 'html' in response_text.lower():
            print("❌ PROBLEM: Received HTML error page!")
            print("   - Server might be returning an error")
            print("   - Check the URL and table name")
            return False
        
        # Try to parse JSON
        try:
            data = response.json()
            print("✅ Successfully parsed JSON!")
            print()
            
            # Analyze JSON structure
            print(f"📊 JSON Type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"📊 Dictionary Keys: {list(data.keys())}")
                
                # Check for common error fields
                if 'error' in data:
                    print(f"❌ API Error: {data['error']}")
                    return False
                
                # Check for data fields
                data_fields = ['data', 'records', 'results', 'items']
                found_data = None
                for field in data_fields:
                    if field in data:
                        found_data = data[field]
                        print(f"✅ Found data in '{field}' field")
                        break
                
                if found_data is not None:
                    if isinstance(found_data, list):
                        print(f"📊 Record count: {len(found_data)}")
                        if len(found_data) > 0:
                            print(f"📊 First record keys: {list(found_data[0].keys()) if isinstance(found_data[0], dict) else 'Not a dict'}")
                    else:
                        print(f"📊 Data type: {type(found_data)}")
                else:
                    print("📊 No standard data field found, treating whole response as data")
                    
            elif isinstance(data, list):
                print(f"📊 List length: {len(data)}")
                if len(data) > 0:
                    print(f"📊 First item type: {type(data[0])}")
                    if isinstance(data[0], dict):
                        print(f"📊 First item keys: {list(data[0].keys())}")
            
            print("✅ API test successful!")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ PROBLEM: JSON parsing failed!")
            print(f"   Error: {str(e)}")
            print("   - Response is not valid JSON")
            print("   - Check if the API returns JSON format")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ PROBLEM: Request timeout!")
        print("   - API server is not responding")
        print("   - Try increasing timeout or check server status")
        return False
    
    except requests.exceptions.ConnectionError:
        print("❌ PROBLEM: Connection error!")
        print("   - Cannot connect to the server")
        print("   - Check if the URL is correct")
        print("   - Check if the server is running")
        return False
    
    except Exception as e:
        print(f"❌ PROBLEM: Unexpected error!")
        print(f"   Error: {str(e)}")
        return False


def main():
    """Main function to test multiple tables"""
    # ✅ Replace with your actual CRM API URL
    CRM_API_URL = "http://localhost/Web_CRM/api.php"  # UPDATE THIS!
    
    # Test different tables
    tables_to_test = [
        'crm_customers',
        'nav_mpesa_transaction', 
        'tickets_full',
        'spl_statistics'
    ]
    
    print("🧪 CRM API Debug Tool")
    print("=" * 60)
    print()
    
    for table in tables_to_test:
        print(f"Testing table: {table}")
        success = test_crm_api(CRM_API_URL, table)
        print()
        print("=" * 60)
        print()
        
        if not success:
            print(f"❌ Failed on table: {table}")
            break
    else:
        print("✅ All tests passed!")


if __name__ == "__main__":
    main()