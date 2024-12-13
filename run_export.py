# leagueapps_auth.py
import jwt
import requests
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LeagueAppsAuth:
    def __init__(self, site_id, client_id, pem_file_path):
        self.site_id = site_id
        self.client_id = client_id
        self.pem_file_path = pem_file_path
        # URLs from the documentation
        self.auth_host = 'https://auth.leagueapps.io'
        self.api_base = 'https://public.leagueapps.io'
        self.access_token = None

    def request_access_token(self):
        """Get access token following their General Steps"""
        logger.debug("Requesting new access token...")
        
        with open(self.pem_file_path, 'r') as f:
            private_key = f.read()

        now = int(time.time())
        claims = {
            'aud': f'{self.auth_host}/v2/auth/token',
            'iss': self.client_id,
            'sub': self.client_id,
            'iat': now,
            'exp': now + 300
        }

        try:
            assertion = jwt.encode(claims, private_key, algorithm='RS256')
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': assertion
            }
            
            auth_url = f'{self.auth_host}/v2/auth/token'
            logger.debug(f"Requesting token from: {auth_url}")
            logger.debug(f"With headers: {headers}")
            logger.debug(f"With data: {data}")
            
            response = requests.post(
                auth_url,
                headers=headers,
                data=data,
                allow_redirects=False  # Prevent redirect to login page
            )
            
            logger.debug(f"Token response status: {response.status_code}")
            logger.debug(f"Token response headers: {dict(response.headers)}")
            logger.debug(f"Token response: {response.text[:500]}...")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                return self.access_token
            else:
                raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error during token request: {str(e)}")
            raise

    def make_request(self, endpoint, params=None):
        """Make an authenticated request to the API"""
        if not self.access_token:
            self.request_access_token()
            
        url = f'{self.api_base}/v2/sites/{self.site_id}/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"Making request to: {url}")
        logger.debug(f"With headers: {headers}")
        logger.debug(f"With params: {params}")
        
        response = requests.get(
            url, 
            params=params, 
            headers=headers,
            allow_redirects=False  # Prevent redirect to login page
        )
        
        if response.status_code == 401:
            logger.debug("Token expired, getting new token...")
            self.access_token = None
            self.request_access_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.get(
                url, 
                params=params, 
                headers=headers,
                allow_redirects=False
            )
            
        response.raise_for_status()
        return response