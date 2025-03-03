import requests
import json

class ProxmoxAPI:
    def __init__(self, host, user, password, realm='pam', verify_ssl=False):
        self.host = host
        self.user = user
        self.password = password
        self.realm = realm
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{host}:8006/api2/json"
        self.ticket = None
        self.csrf_token = None

    def authenticate(self):
        """Authenticate with Proxmox API and get ticket and CSRF token"""
        auth_url = f"{self.base_url}/access/ticket"
        data = {
            'username': f"{self.user}@{self.realm}",
            'password': self.password
        }
        
        try:
            response = requests.post(auth_url, data=data, verify=self.verify_ssl)
            if response.status_code == 200:
                result = response.json()['data']
                self.ticket = result['ticket']
                self.csrf_token = result['CSRFPreventionToken']
                return True
            else:
                print(f"Authentication failed: {response.text}")
                return False
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False
    
    def api_request(self, method, endpoint, data=None):
        """Make a request to the Proxmox API"""
        if not self.ticket:
            if not self.authenticate():
                return {"success": False, "message": "Authentication failed"}
        
        url = f"{self.base_url}/{endpoint}"
        headers = {'Cookie': f"PVEAuthCookie={self.ticket}"}
        
        if method in ['POST', 'PUT', 'DELETE']:
            headers['CSRFPreventionToken'] = self.csrf_token
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, verify=self.verify_ssl)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=data, verify=self.verify_ssl)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, data=data, verify=self.verify_ssl)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, verify=self.verify_ssl)
            else:
                return {"success": False, "message": f"Unsupported method: {method}"}
            
            if response.status_code in [200, 201, 202]:
                return {"success": True, "data": response.json()['data']}
            else:
                return {"success": False, "message": response.text}
        except Exception as e:
            return {"success": False, "message": str(e)}
