"""
Service for fetching Greenbook/Tealbook data from Philadelphia Fed.
"""
import logging
import requests
from datetime import datetime
from pathlib import Path
import tempfile
from typing import Dict, Optional
import zipfile
import io
import pandas as pd
import json

from src.macroeconomic_data.aws.bucket_manager import BucketManager

logger = logging.getLogger(__name__)

class GreenBookDataFetcher:
    """Service for fetching and managing Greenbook/Tealbook forecast data."""
    
    BASE_URL = "https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/greenbook-data/GBweb"
    BUCKET_NAME = "greenbook-forecasts"
    
    VARIABLES = {
        'all': 'All_Variables',
        'rgdp': 'gRGDP',
        'pgdp': 'gPGDP',
        'unemp': 'UNEMP',
        'cpi': 'gPCPI',
        'core_cpi': 'gPCPIX',
        'pce': 'gPPCE',
        'core_pce': 'gPPCEX',
        'consumption': 'gRPCE',
        'business_investment': 'gRBF',
        'residential_investment': 'gRRES',
        'federal_govt': 'gRGOVF',
        'state_local_govt': 'gRGOVSL',
        'nominal_gdp': 'gNGDP',
        'housing_starts': 'HSTART',
        'industrial_production': 'gIP'
    }

    def __init__(self):
        """Initialize the data fetcher."""
        self.bucket_manager = BucketManager(bucket_name=self.BUCKET_NAME)

    def _construct_download_url(self, variable_code: str, is_documentation: bool = False) -> str:
        """Construct the download URL for a specific variable or documentation."""
        if is_documentation:
            return f"{self.BASE_URL}/Documentation.pdf"
        return f"{self.BASE_URL}/Gbweb%5F{variable_code}%5FColumn%5FFormat.zip"

    def _download_file(self, url: str) -> Optional[bytes]:
        """Download a file from the given URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Error downloading file from {url}: {str(e)}")
            return None

    def _get_metadata(self, variable_name: str, filename: str) -> Dict:
        """Create metadata for the downloaded file."""
        if filename == "Documentation.pdf":
            return {
                'file_type': 'documentation',
                'source': 'Philadelphia Fed Greenbook/Tealbook',
                'description': 'Technical documentation for Greenbook/Tealbook data sets',
                'download_date': datetime.utcnow().isoformat(),
                'last_modified': datetime.utcnow().isoformat(),
                'format': 'pdf',
                'documentation_url': 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/philadelphia-data-set'
            }

        variable_descriptions = {
            'rgdp': 'Real GDP (Q/Q Growth; Annualized Percentage Points)',
            'pgdp': 'GDP Price Inflation (Q/Q; Annualized Percentage Points)',
            'unemp': 'Unemployment Rate (Level; Percentage Points)',
            'cpi': 'Headline CPI Inflation (Q/Q; Annualized Percentage Points)',
            'core_cpi': 'Core CPI Inflation (Q/Q; Annualized Percentage Points)',
            'pce': 'Headline PCE Inflation (Q/Q; Annualized Percentage Points)',
            'core_pce': 'Core PCE Inflation (Q/Q; Annualized Percentage Points)',
            'consumption': 'Real Personal Consumption Expenditures (Q/Q Growth; Annualized Percentage Points)',
            'business_investment': 'Real Business Fixed Investment (Q/Q Growth; Annualized Percentage Points)',
            'residential_investment': 'Real Residential Investment (Q/Q Growth; Annualized Percentage Points)',
            'federal_govt': 'Real Federal Government C and GI (Q/Q Growth; Annualized Percentage Points)',
            'state_local_govt': 'Real State and Local Government C and GI (Q/Q Growth; Annualized Percentage Points)',
            'nominal_gdp': 'Nominal GDP (Q/Q Growth; Annualized Percentage Points)',
            'housing_starts': 'Housing Starts (Level; Millions of Units; Annual Rate)',
            'industrial_production': 'Industrial Production Index (Q/Q Growth; Annualized Percentage Points)',
            'all': 'All Variables Combined Dataset'
        }

        return {
            # Variable Information
            'variable_name': variable_name,
            'variable_code': self.VARIABLES[variable_name],
            'variable_description': variable_descriptions[variable_name],
            'frequency': 'Quarterly',
            'units': variable_descriptions[variable_name].split('(')[-1].strip(')'),
            
            # Source Information
            'source': 'Philadelphia Fed Greenbook/Tealbook',
            'source_description': 'Federal Reserve Board of Governors Staff Forecasts',
            'data_type': 'Historical and Forecast Values',
            'forecast_horizon': 'Up to 9 quarters ahead',
            'publication_lag': '5 years',
            
            # File Information
            'original_filename': filename,
            'format': filename.split('.')[-1].lower(),
            'download_date': datetime.utcnow().isoformat(),
            'last_modified': datetime.utcnow().isoformat(),
            
            # Data Structure
            'structure': ('Each row corresponds to a different Tealbook/Greenbook publication date. '
                        'Columns give historical values and forecasts for that publication.'),
            'time_coverage': ('For each publication: up to 4 quarters of history before nowcast, '
                            'nowcast quarter, and up to 9 quarters of forecasts'),
            
            # Additional Information
            'documentation_url': 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/philadelphia-data-set',
            'notes': ('Data is released with a 5-year lag. Values include both historical data '
                     'and staff forecasts as they appeared at the time of each FOMC meeting.')
        }

    def _download_documentation(self) -> bool:
        """Download and store the documentation PDF."""
        logger.info("Downloading documentation file...")
        url = self._construct_download_url("", is_documentation=True)
        content = self._download_file(url)
        
        if not content:
            return False
            
        try:
            success = self.bucket_manager.upload_file(
                file_content=content,
                file_path="Documentation.pdf",
                metadata=self._get_metadata("", "Documentation.pdf")
            )
            
            if success:
                logger.info("Successfully stored documentation file")
            else:
                logger.error("Failed to store documentation file")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing documentation file: {str(e)}")
            return False

    def _get_file_description(self, filename: str) -> str:
        """Get a human-readable description from a filename."""
        # Remove extension
        name = filename.rsplit('.', 1)[0]
        
        # Split by underscore
        parts = name.split('_')
        if len(parts) >= 3:
            var_code = parts[0]
            start_year = parts[1]
            end_year = parts[2]
            if end_year.lower() == 'last':
                end_year = 'Present'
            return f"{var_code} ({start_year} to {end_year})"
        
        return filename

    def _save_locally(self, content: bytes, variable_code: str, filename: str, metadata: dict) -> bool:
        """Save file and metadata locally."""
        try:
            # Create base directory
            base_dir = Path('data/green_book') / variable_code / filename.rsplit('.', 1)[0]
            base_dir.mkdir(parents=True, exist_ok=True)
            
            # Save data file
            data_path = base_dir / f"data.{filename.split('.')[-1]}"
            data_path.write_bytes(content)
            
            # Save metadata
            metadata_path = base_dir / "metadata.txt"
            with metadata_path.open('w') as f:
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
            
            return True
        except Exception as e:
            logger.error(f"Error saving files locally: {str(e)}")
            return False

    def _extract_and_store_zip(self, zip_content: bytes, variable_key: str, variable_code: str) -> bool:
        """Extract ZIP contents and store files in S3."""
        try:
            # Create ZIP file in memory
            zip_buffer = io.BytesIO(zip_content)
            
            with zipfile.ZipFile(zip_buffer) as zip_ref:
                # List all files in the ZIP
                files = zip_ref.namelist()
                
                # Filter out any non-data files (like README or documentation)
                data_files = [f for f in files if f.endswith(('.csv', '.xlsx'))]
                
                if len(data_files) > 1:
                    print("\nMultiple datasets found. Please choose one:")
                    for idx, filename in enumerate(data_files, 1):
                        description = self._get_file_description(filename)
                        print(f"{idx}. {description}")
                    
                    while True:
                        try:
                            choice = int(input("\nEnter number (0 to cancel): "))
                            if choice == 0:
                                return False
                            if 1 <= choice <= len(data_files):
                                selected_files = [data_files[choice - 1]]
                                break
                            print("Invalid choice. Please try again.")
                        except ValueError:
                            print("Please enter a valid number.")
                else:
                    selected_files = data_files

                success = True
                for filename in selected_files:
                    logger.info(f"Extracting {filename} from ZIP...")
                    
                    # Read file content from ZIP as binary
                    with zip_ref.open(filename) as file:
                        file_content = file.read()
                    
                    # Get base directory for this file
                    base_dir = f"{variable_code}/{filename.rsplit('.', 1)[0]}"
                    
                    # Save to S3
                    # Save data file
                    data_path = f"{base_dir}/data.{filename.split('.')[-1]}"
                    file_success = self.bucket_manager.upload_file(
                        file_content=file_content,
                        file_path=data_path,
                        metadata={'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if filename.endswith('.xlsx') else 'text/csv'}
                    )
                    
                    if not file_success:
                        logger.error(f"Failed to store {filename} in S3")
                        success = False
                        continue
                    
                    # Save metadata
                    metadata = self._get_metadata(variable_key, filename)
                    metadata_path = f"{base_dir}/metadata.json"
                    metadata_success = self.bucket_manager.upload_file(
                        file_content=json.dumps(metadata, indent=2).encode(),
                        file_path=metadata_path,
                        metadata={'content_type': 'application/json'}
                    )
                    
                    if not metadata_success:
                        logger.error(f"Failed to store metadata for {filename} in S3")
                        success = False
                        continue
                    
                    # Save locally
                    local_success = self._save_locally(file_content, variable_code, filename, metadata)
                    if local_success:
                        logger.info(f"Successfully stored {filename} locally and in S3")
                    else:
                        logger.error(f"Failed to store {filename} locally")
                        success = False
                        
                return success
                
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid ZIP file for {variable_key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error processing ZIP file for {variable_key}: {str(e)}")
            return False

    def download_and_store_variable(self, variable_key: str, force_download: bool = True) -> bool:
        """Download and store a specific variable's data."""
        # Handle full variable keys (e.g., 'gdp.real_gdp')
        if '.' in variable_key:
            main_key, sub_key = variable_key.split('.')
            # Convert to the actual key format
            if main_key == 'gdp' and sub_key == 'real_gdp':
                variable_key = 'rgdp'
            elif main_key == 'gdp' and sub_key == 'price_gdp':
                variable_key = 'pgdp'
            elif main_key == 'cpi':
                if sub_key == 'core':
                    variable_key = 'core_cpi'
                elif sub_key == 'headline':
                    variable_key = 'cpi'
            elif main_key == 'pce':
                if sub_key == 'core':
                    variable_key = 'core_pce'
                elif sub_key == 'headline':
                    variable_key = 'pce'
            
        variable_code = self.VARIABLES.get(variable_key)
        if not variable_code:
            logger.error(f"Unknown variable key: {variable_key}")
            return False

        # Print which series we're downloading
        print(f"\n📊 Downloading series: {variable_code}")
        print(f"📝 Description: {self._get_metadata(variable_key, '')['variable_description']}\n")

        # Always download the ZIP file if force_download is True
        if force_download:
            url = self._construct_download_url(variable_code)
            content = self._download_file(url)
            
            if not content:
                return False

            return self._extract_and_store_zip(content, variable_key, variable_code)
        else:
            # Check if files exist in bucket
            contents = self.bucket_manager.get_contents()
            variable_files = [item for item in contents if item['Key'].startswith(f"{variable_code}/")]
            
            if not variable_files:
                # No files found, download and extract
                url = self._construct_download_url(variable_code)
                content = self._download_file(url)
                
                if not content:
                    return False

                return self._extract_and_store_zip(content, variable_key, variable_code)
            
            return True

    def download_all_variables(self) -> Dict[str, bool]:
        """Download and store all available variables."""
        results = {'documentation': self._download_documentation()}
        
        for variable_key in self.VARIABLES.keys():
            logger.info(f"Downloading {variable_key}...")
            success = self.download_and_store_variable(variable_key)
            results[variable_key] = success
        return results

    def check_for_updates(self) -> Dict[str, bool]:
        """Check for updates in the data and download if necessary."""
        results = {}
        
        # Check documentation first
        try:
            metadata = self.bucket_manager.get_metadata("Documentation.pdf")
            if metadata:
                last_modified = datetime.fromisoformat(metadata.get('last_modified', '2000-01-01'))
                if (datetime.utcnow() - last_modified).days >= 30:
                    logger.info("Updating documentation...")
                    results['documentation'] = self._download_documentation()
            else:
                logger.info("Documentation not found, downloading...")
                results['documentation'] = self._download_documentation()
        except Exception as e:
            logger.error(f"Error checking documentation updates: {str(e)}")
            results['documentation'] = False
        
        # Check variables
        for variable_key, variable_code in self.VARIABLES.items():
            # We'll check the first file in the directory
            try:
                # List contents of the variable's directory
                contents = self.bucket_manager.get_contents()
                variable_files = [item for item in contents if item['Key'].startswith(f"{variable_code}/")]
                
                if variable_files:
                    # Get metadata of the first file
                    first_file = variable_files[0]
                    metadata = self.bucket_manager.get_metadata(first_file['Key'])
                    
                    if metadata:
                        last_modified = datetime.fromisoformat(metadata.get('last_modified', '2000-01-01'))
                        if (datetime.utcnow() - last_modified).days >= 30:  # Check monthly
                            logger.info(f"Updating {variable_key} data...")
                            success = self.download_and_store_variable(variable_key)
                            results[variable_key] = success
                    else:
                        # No metadata, update the files
                        logger.info(f"No metadata found for {variable_key}, downloading...")
                        success = self.download_and_store_variable(variable_key)
                        results[variable_key] = success
                else:
                    # No files exist, download them
                    logger.info(f"No files found for {variable_key}, downloading...")
                    success = self.download_and_store_variable(variable_key)
                    results[variable_key] = success
                    
            except Exception as e:
                logger.error(f"Error checking updates for {variable_key}: {str(e)}")
                results[variable_key] = False
                
        return results 

    def get_variable_data(self, variable_code: str) -> Optional[pd.DataFrame]:
        """Get variable data from S3 and convert to DataFrame."""
        try:
            # List contents of the variable's directory
            contents = self.bucket_manager.get_contents()
            variable_files = [item for item in contents if item['Key'].startswith(f"{variable_code}/")]
            
            if not variable_files:
                logger.error(f"No data found for {variable_code}")
                return None
            
            # Find the data file (should be a CSV or Excel)
            data_file = next((f for f in variable_files if f['Key'].endswith(('.csv', '.xlsx'))), None)
            if not data_file:
                logger.error(f"No data file found for {variable_code}")
                return None
            
            # Read the file content
            content = self.bucket_manager.get_content(data_file['Key'])
            if not content:
                return None
            
            # Convert to DataFrame
            if data_file['Key'].endswith('.csv'):
                return pd.read_csv(io.BytesIO(content.read()))
            else:  # Excel
                return pd.read_excel(io.BytesIO(content.read()))
        except Exception as e:
            logger.error(f"Error getting variable data: {str(e)}")
            return None 