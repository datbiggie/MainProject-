import requests
import json

# Test the login_ajax endpoint
url = 'http://localhost:8000/ecommerce/login-ajax/'

# Test data
data = {
    'login_email': 'test@example.com',
    'login_password': 'testpassword'
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Content: {response.text}")
    
    if response.status_code == 200:
        try:
            json_response = response.json()
            print(f"JSON Response: {json_response}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
    else:
        print(f"HTTP Error: {response.status_code}")
        
except requests.exceptions.ConnectionError as e:
    print(f"Connection Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}") 