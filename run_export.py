#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import logging
from leagueapps_auth import LeagueAppsAuth
from registration_exporter import RegistrationExporter

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration from environment variables
    site_id = os.getenv('LEAGUEAPPS_SITE_ID')
    client_id = os.getenv('LEAGUEAPPS_CLIENT_ID')
    pem_path = os.getenv('LEAGUEAPPS_PEM_PATH')
    
    if not all([site_id, client_id, pem_path]):
        logger.error("Missing required environment variables!")
        print("""
Please check your .env file has the following variables:
LEAGUEAPPS_SITE_ID=your_site_id
LEAGUEAPPS_CLIENT_ID=your_client_id
LEAGUEAPPS_PEM_PATH=/path/to/your/private_key.pem
        """)
        return
    
    try:
        # Initialize the auth handler
        logger.info("Initializing LeagueApps authentication...")
        auth = LeagueAppsAuth(
            site_id=int(site_id),  # Convert site_id to integer
            client_id=client_id,
            pem_file_path=pem_path
        )
        
        # Initialize and run the exporter
        logger.info("Starting export process...")
        exporter = RegistrationExporter(auth)
        filepath = exporter.run_export()
        
        if filepath:
            print(f"\nExport completed successfully!")
            print(f"Output file: {filepath}")
        else:
            print("\nExport completed but no data was retrieved.")
            
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()