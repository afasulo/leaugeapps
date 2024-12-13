import pandas as pd
from datetime import datetime
import os
import time
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RegistrationExporter:
    def __init__(self, auth_handler):
        self.auth = auth_handler
        self.base_endpoint = "registrations-2"
        
    def fetch_all_registrations(self, include_deleted: bool = True) -> List[Dict[Any, Any]]:
        """
        Fetches all registrations using pagination with last-updated and last-id parameters
        """
        all_registrations = []
        last_updated = 0
        last_id = 0
        page = 1
        
        while True:
            logger.debug(f"Fetching page {page} with last_updated={last_updated}, last_id={last_id}")
            
            params = {
                'last-updated': last_updated,
                'last-id': last_id,
                'includeDeleted': str(include_deleted).lower()
            }
            
            try:
                response = self.auth.make_request(
                    endpoint=self.base_endpoint,
                    params=params
                )
                
                # Parse JSON response
                registrations = response.json()
                
                logger.debug(f"Retrieved {len(registrations)} registrations")
                
                if not registrations:  # No more results
                    break
                    
                all_registrations.extend(registrations)
                
                # Update pagination parameters from last record
                last_record = registrations[-1]
                if 'lastUpdated' in last_record:
                    last_updated = last_record['lastUpdated']
                if 'id' in last_record:
                    last_id = last_record['id']
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching registrations: {str(e)}")
                raise
            
        logger.info(f"Total registrations fetched: {len(all_registrations)}")
        return all_registrations

    def process_registrations(self, registrations: List[Dict[Any, Any]]) -> pd.DataFrame:
        """
        Convert registrations list to pandas DataFrame and process data
        """
        # Filter out completely deleted records that only contain deletion info
        active_registrations = [
            reg for reg in registrations 
            if not (len(reg.keys()) <= 3 and 'deleted' in reg)
        ]
        
        df = pd.DataFrame(active_registrations)
        
        # Convert timestamp columns to datetime
        timestamp_columns = [
            'lastUpdated', 'created', 'birthDate', 'programStartDate', 
            'programEndDate', 'registrationStartDate', 'registrationEndDate',
            'lastPaymentDate', 'waiverAcceptedTimestamp', 'deletedOn'
        ]
        
        for col in timestamp_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], unit='ms')
        
        return df

    def export_to_csv(self, df: pd.DataFrame, output_dir: str = "exports") -> str:
        """
        Export DataFrame to CSV with timestamp in filename
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"registrations_export_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(df)} registrations to {filepath}")
        return filepath

    def run_export(self) -> str:
        """
        Run the complete export process
        """
        logger.info("Starting registration export...")
        
        try:
            logger.info("Fetching registrations...")
            registrations = self.fetch_all_registrations()
            logger.info(f"Retrieved {len(registrations)} registrations")
            
            if not registrations:
                logger.warning("No registrations were retrieved!")
                return None
            
            logger.info("Processing data...")
            df = self.process_registrations(registrations)
            
            logger.info("Exporting to CSV...")
            filepath = self.export_to_csv(df)
            logger.info(f"Export completed: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise