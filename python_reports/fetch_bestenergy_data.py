"""
Best.Energy API Data Fetcher
Fetches energy data from Best.Energy API and formats it for VEM report generation
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class BestEnergyDataFetcher:
    """Fetch and format data from Best.Energy API for VEM reports"""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        Initialize the data fetcher
        
        Args:
            api_url: Best.Energy API base URL (or from .env)
            api_key: API authentication key (or from .env)
        """
        self.api_url = api_url or os.getenv('VITE_BEST_ENERGY_API_URL', 'https://api.best.energy')
        self.api_key = api_key or os.getenv('VITE_BEST_ENERGY_API_KEY', '')
        self.timeout = int(os.getenv('VITE_API_TIMEOUT', '30000')) / 1000  # Convert to seconds
        
        if not self.api_key:
            print("⚠️  Warning: No API key found. Set VITE_BEST_ENERGY_API_KEY in .env")
        
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
    
    def fetch_customer_data(self, customer_id: str, 
                           start_date: str, end_date: str,
                           output_csv: str = 'energy_data.csv') -> pd.DataFrame:
        """
        Fetch customer energy data and save to CSV in VEM format
        
        Args:
            customer_id: Customer/Site ID (e.g., 'wilson-center')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            output_csv: Output CSV filename
            
        Returns:
            DataFrame with Timestamp, Usage_kWh, Asset_Name columns
        """
        print(f"🔄 Fetching data for customer: {customer_id}")
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"🌐 API URL: {self.api_url}")
        
        try:
            # Fetch consumption data
            consumption_data = self._fetch_consumption(customer_id, start_date, end_date)
            
            if not consumption_data:
                print("❌ No data received from API")
                return pd.DataFrame()
            
            # Transform to VEM format
            df = self._transform_to_vem_format(consumption_data)
            
            # Save to CSV
            df.to_csv(output_csv, index=False)
            print(f"✅ Data saved to: {output_csv}")
            print(f"📊 Total records: {len(df):,}")
            print(f"📊 Unique assets: {df['Asset_Name'].nunique()}")
            print(f"📊 Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request Error: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise
    
    def _fetch_consumption(self, customer_id: str, 
                          start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch consumption data from Best.Energy/Eniscope API
        
        Based on Wilson Center data structure: channels with readings
        """
        # Convert dates to Unix timestamps (Eniscope uses Unix time)
        start_ts = int(pd.to_datetime(start_date).timestamp())
        end_ts = int(pd.to_datetime(end_date).timestamp())
        
        # Eniscope API endpoint patterns
        endpoints = [
            # Standard Eniscope Core API v1
            f'/v1/readings/{customer_id}',
            f'/readings/{customer_id}',
            f'/api/v1/readings/{customer_id}',
            
            # Channel-based endpoints
            f'/v1/channels/{customer_id}/readings',
            f'/channels/{customer_id}/readings',
            
            # Site-based endpoints
            f'/v1/sites/{customer_id}/data',
            f'/sites/{customer_id}/readings',
            
            # Alternative patterns
            f'/v1/devices/{customer_id}/readings',
            f'/data/{customer_id}',
        ]
        
        params = {
            'start': start_ts,
            'end': end_ts,
            'resolution': '3600',  # Hourly data
            'from': start_ts,
            'to': end_ts,
            'startTime': start_ts,
            'endTime': end_ts,
        }
        
        for endpoint in endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                print(f"🔍 Trying endpoint: {endpoint}")
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Got response from: {endpoint}")
                    
                    # Handle different response structures
                    if isinstance(data, dict):
                        # Extract data from common wrapper patterns
                        if 'data' in data:
                            return data['data']
                        elif 'items' in data:
                            return data['items']
                        elif 'results' in data:
                            return data['results']
                        else:
                            return [data]
                    elif isinstance(data, list):
                        return data
                    
                elif response.status_code == 404:
                    continue  # Try next endpoint
                else:
                    print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Endpoint {endpoint} failed: {str(e)}")
                continue
        
        # If all endpoints fail, try to use mock data or provide guidance
        print("\n❌ All API endpoints failed.")
        print("📝 Please check:")
        print("   1. Your API key is correct in .env")
        print("   2. The customer_id is correct")
        print("   3. Review 'Core API v1.pdf' for actual endpoint paths")
        print("   4. Or use generate_mock_data() to create sample data for testing")
        
        return []
    
    def _transform_to_vem_format(self, data: List[Dict]) -> pd.DataFrame:
        """
        Transform Eniscope API response to VEM CSV format
        
        Expected Eniscope format:
        {
            "channels": [
                {
                    "channel": "RTU-2_WCDS_Wilson Ctr",
                    "rawReadings": [
                        {"ts": 1764565200, "E": 1290.08, "P": 1290.12, ...}
                    ]
                }
            ]
        }
        
        VEM Output format:
            Timestamp, Usage_kWh, Asset_Name
        """
        records = []
        
        # Handle different response structures
        channels_list = []
        
        if isinstance(data, dict):
            # Response is wrapped in object
            channels_list = data.get('channels', [])
            if not channels_list and 'rawReadings' in data:
                # Single channel response
                channels_list = [data]
        elif isinstance(data, list):
            # Response is array of channels
            channels_list = data
        
        # Process each channel
        for channel_data in channels_list:
            asset_name = (
                channel_data.get('channel') or
                channel_data.get('channelName') or
                channel_data.get('deviceName') or
                channel_data.get('name') or
                'Unknown Asset'
            )
            
            # Get readings
            readings = (
                channel_data.get('rawReadings') or
                channel_data.get('readings') or
                channel_data.get('data') or
                []
            )
            
            # Process each reading
            for reading in readings:
                # Get timestamp (Unix timestamp or ISO string)
                ts = reading.get('ts') or reading.get('timestamp')
                if ts:
                    # Convert Unix timestamp to datetime
                    if isinstance(ts, (int, float)):
                        timestamp = pd.to_datetime(ts, unit='s')
                    else:
                        timestamp = pd.to_datetime(ts)
                    
                    # Get energy value (E field in Eniscope data)
                    # E is in Wh, convert to kWh
                    usage_kwh = (
                        reading.get('E') or          # Eniscope energy field
                        reading.get('energy') or
                        reading.get('P') or          # Power if energy not available
                        reading.get('power') or
                        reading.get('value') or
                        reading.get('kwh') or
                        0
                    )
                    
                    # Eniscope stores in Wh, convert to kWh
                    if usage_kwh > 100:  # Likely in Wh
                        usage_kwh = usage_kwh / 1000.0
                    
                    records.append({
                        'Timestamp': timestamp,
                        'Usage_kWh': float(usage_kwh),
                        'Asset_Name': str(asset_name)
                    })
        
        df = pd.DataFrame(records)
        
        if not df.empty:
            # Ensure timestamp is datetime
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            # Sort by timestamp and asset
            df = df.sort_values(['Timestamp', 'Asset_Name'])
        
        return df
    
    def fetch_sites_list(self, customer_id: str = None) -> List[Dict]:
        """Fetch list of available sites/assets"""
        endpoints = [
            f'/customers/{customer_id}/sites' if customer_id else '/sites',
            f'/v1/customers/{customer_id}/sites' if customer_id else '/v1/sites',
            '/customers' if not customer_id else f'/customers/{customer_id}',
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'items' in data:
                        return data['items']
                    elif isinstance(data, list):
                        return data
                    else:
                        return [data]
                        
            except Exception as e:
                continue
        
        return []
    
    def generate_mock_data(self, customer_id: str,
                          start_date: str, end_date: str,
                          output_csv: str = 'energy_data.csv',
                          assets: List[str] = None) -> pd.DataFrame:
        """
        Generate realistic mock data for testing when API is not available
        
        Args:
            customer_id: Site identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            output_csv: Output CSV filename
            assets: List of asset names (defaults to common HVAC assets)
        """
        print("🔧 Generating mock data for testing...")
        
        if assets is None:
            assets = ['RTU-1', 'RTU-2', 'Kitchen Equipment', 'Lighting', 'Plug Loads']
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Generate hourly timestamps
        timestamps = pd.date_range(start=start, end=end, freq='H')
        
        records = []
        for timestamp in timestamps:
            hour = timestamp.hour
            weekday = timestamp.weekday()
            
            for asset in assets:
                # Create realistic usage patterns
                base_usage = {
                    'RTU-1': 150,
                    'RTU-2': 140,
                    'Kitchen Equipment': 80,
                    'Lighting': 50,
                    'Plug Loads': 30
                }.get(asset, 100)
                
                # Add time-of-day variation
                if 6 <= hour <= 18:  # Operating hours
                    usage_multiplier = 1.5
                elif 19 <= hour <= 22:  # Evening
                    usage_multiplier = 1.2
                else:  # Night
                    usage_multiplier = 0.6
                
                # Add day-of-week variation
                if weekday >= 5:  # Weekend
                    usage_multiplier *= 0.7
                
                # Add some randomness
                import random
                usage = base_usage * usage_multiplier * random.uniform(0.85, 1.15)
                
                records.append({
                    'Timestamp': timestamp,
                    'Usage_kWh': round(usage, 2),
                    'Asset_Name': asset
                })
        
        df = pd.DataFrame(records)
        df.to_csv(output_csv, index=False)
        
        print(f"✅ Mock data generated: {output_csv}")
        print(f"📊 Total records: {len(df):,}")
        print(f"📊 Assets: {', '.join(assets)}")
        print(f"📊 Period: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
        
        return df


def main():
    """Main function to fetch data"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch Best.Energy data for VEM reports')
    parser.add_argument('--customer-id', default='wilson-center', help='Customer/Site ID')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='energy_data.csv', help='Output CSV file')
    parser.add_argument('--mock', action='store_true', help='Generate mock data instead of fetching')
    
    args = parser.parse_args()
    
    fetcher = BestEnergyDataFetcher()
    
    if args.mock:
        # Generate mock data for testing
        df = fetcher.generate_mock_data(
            customer_id=args.customer_id,
            start_date=args.start_date,
            end_date=args.end_date,
            output_csv=args.output
        )
    else:
        # Fetch real data from API
        df = fetcher.fetch_customer_data(
            customer_id=args.customer_id,
            start_date=args.start_date,
            end_date=args.end_date,
            output_csv=args.output
        )
    
    if not df.empty:
        print("\n" + "="*60)
        print("📊 DATA PREVIEW")
        print("="*60)
        print(df.head(10))
        print("\n" + "="*60)
        print("✅ Ready for VEM report generation!")
        print(f"   Run: python generate_vem_report.py")
        print("="*60)
    else:
        print("\n⚠️  No data was collected. Use --mock flag for testing.")


if __name__ == "__main__":
    main()

