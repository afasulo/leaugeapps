# leagueapps_auth.py
import jwt
import requests
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LeagueAppsAuth:
    def __init__(self, site_id, client_id, pem_file_path):
        self.site_id = site_id
        self.client_id = client_id
        self.pem_file_path = pem_file_path
        self.auth_host = 'https://auth.leagueapps.io'
        self.api_base = 'https://public.leagueapps.io'
        self.access_token = None

    def request_access_token(self):
        """Get access token using JWT assertion"""
        try:
            # Read the private key
            with open(self.pem_file_path, 'r') as f:
                private_key = f.read()

            # Create JWT claims
            now = int(time.time())
            claims = {
                'aud': 'https://auth.leagueapps.io/v2/auth/token',
                'iss': self.client_id,
                'sub': self.client_id,
                'iat': now,
                'exp': now + 300
            }

            # Create JWT
            assertion = jwt.encode(claims, private_key, algorithm='RS256')
            
            # Set up auth request
            auth_url = f'{self.auth_host}/v2/auth/token'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': assertion
            }
            
            logger.debug(f"Making auth request to: {auth_url}")
            logger.debug(f"With client_id: {self.client_id}")
            
            # Make the request
            response = requests.post(
                auth_url,
                headers=headers,
                data=data,
                allow_redirects=False  # Important: don't follow redirects
            )
            
            logger.debug(f"Auth response status: {response.status_code}")
            logger.debug(f"Auth response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                return self.access_token
            else:
                logger.error(f"Auth request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error during token request: {str(e)}")
            raise

    def make_request(self, endpoint, params=None):
        """Make an authenticated request to the API"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            if not self.access_token:
                self.request_access_token()
                if not self.access_token:
                    raise Exception("Failed to obtain access token")
            
            url = f'{self.api_base}/v2/sites/{self.site_id}/export/{endpoint}'
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            logger.debug(f"Making API request to: {url}")
            logger.debug(f"With params: {params}")
            
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    allow_redirects=False
                )
                
                if response.status_code == 401:
                    logger.debug("Token expired, refreshing...")
                    self.access_token = None
                    retry_count += 1
                    continue
                    
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if retry_count == max_retries - 1:
                    raise
                retry_count += 1
                time.sleep(1)  # Wait a second before retrying
                
        raise Exception("Max retries reached")
    