import pandas as pd
from datetime import datetime
import os
import time
from typing import List, Dict, Any

class RegistrationExporter:
    def __init__(self, auth_handler):
        self.auth = auth_handler
        self.base_endpoint = f"/sites/{self.auth.site_id}/export/registrations-2"
        
    def fetch_all_registrations(self, include_deleted: bool = True) -> List[Dict[Any, Any]]:
        """
        Fetches all registrations using pagination with last-updated and last-id parameters
        """
        all_registrations = []
        last_updated = 0
        last_id = 0
        
        while True:
            params = {
                'last-updated': last_updated,
                'last-id': last_id,
                'includeDeleted': str(include_deleted).lower()
            }
            
            response = self.auth.make_request(
                endpoint=self.base_endpoint,
                params=params
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch registrations: {response.text}")
                
            registrations = response.json()
            
            if not registrations:  # No more results
                break
                
            all_registrations.extend(registrations)
            
            # Update pagination parameters from last record
            last_record = registrations[-1]
            last_updated = last_record.get('lastUpdated', last_updated)
            last_id = last_record.get('id', last_id)
            
            # Add small delay to avoid rate limiting
            time.sleep(0.1)
            
        return all_registrations

    def process_registrations(self, registrations: List[Dict[Any, Any]]) -> pd.DataFrame:
        """
        Convert registrations list to pandas DataFrame and process data
        """
        df = pd.DataFrame(registrations)
        
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
        # Create exports directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"registrations_export_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Export to CSV
        df.to_csv(filepath, index=False)
        return filepath

    def run_export(self) -> str:
        """
        Run the complete export process
        """
        print("Fetching registrations...")
        registrations = self.fetch_all_registrations()
        print(f"Retrieved {len(registrations)} registrations")
        
        print("Processing data...")
        df = self.process_registrations(registrations)
        
        print("Exporting to CSV...")
        filepath = self.export_to_csv(df)
        print(f"Export completed: {filepath}")
        
        return filepath