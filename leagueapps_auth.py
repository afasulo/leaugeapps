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
        self.auth_host = 'https://auth.leagueapps.io'
        self.api_base = 'https://public.leagueapps.io'
        self.access_token = None

        # Validate the key on initialization
        try:
            with open(self.pem_file_path, 'r') as f:
                self.private_key = f.read()
                if '-----BEGIN PRIVATE KEY-----' not in self.private_key:
                    raise ValueError("PEM file does not contain a valid private key")
        except Exception as e:
            raise Exception(f"Failed to load private key: {str(e)}")

    def create_jwt(self):
        """Create JWT with proper headers for PKCS#8 key"""
        now = int(time.time())
        claims = {
            'aud': f'{self.auth_host}/v2/auth/token',
            'iss': self.client_id,
            'sub': self.client_id,
            'iat': now,
            'exp': now + 300
        }
        
        # Headers explicitly specify the algorithm
        headers = {
            'alg': 'RS256',
            'typ': 'JWT'
        }
        
        try:
            return jwt.encode(
                claims,
                self.private_key,
                algorithm='RS256',
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to create JWT: {str(e)}")
            raise

    def request_access_token(self):
        """Get access token using JWT assertion"""
        try:
            assertion = self.create_jwt()
            
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
            logger.debug(f"Request headers: {headers}")
            
            response = requests.post(
                auth_url,
                headers=headers,
                data=data,
                allow_redirects=False
            )
            
            logger.debug(f"Token response status: {response.status_code}")
            logger.debug(f"Token response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    token_data = response.json()
                    self.access_token = token_data['access_token']
                    return self.access_token
                except Exception as e:
                    logger.error(f"Failed to parse token response: {str(e)}")
                    logger.debug(f"Response content: {response.text[:1000]}")
                    raise
            else:
                raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error during token request: {str(e)}")
            raise

    def make_request(self, endpoint, params=None):
        """Make an authenticated request to the API"""
        if not self.access_token:
            self.request_access_token()
            
        if not endpoint.startswith('export/'):
            endpoint = f'export/{endpoint}'
            
        url = f'{self.api_base}/v2/sites/{self.site_id}/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"Making API request to: {url}")
        logger.debug(f"Request headers: {headers}")
        logger.debug(f"Request params: {params}")
        
        try:
            response = requests.get(
                url, 
                params=params, 
                headers=headers,
                allow_redirects=False
            )
            
            logger.debug(f"API response status: {response.status_code}")
            logger.debug(f"API response headers: {dict(response.headers)}")
            
            if response.status_code == 401:
                logger.debug("Token expired, refreshing...")
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
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise