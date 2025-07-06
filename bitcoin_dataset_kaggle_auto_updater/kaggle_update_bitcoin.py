import os
# Disable resumable uploads (helpful in CI environments)
os.environ["KAGGLE_API_NO_RESUME"] = "True"

import sys
import time
import shutil
import pandas as pd
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi

# Load environment variables
load_dotenv()

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Configure proxy settings (will be used for Binance API calls)
proxies = {
    'http': os.getenv('HTTP_PROXY'),
    'https': os.getenv('HTTPS_PROXY')
}

def create_binance_client(max_retries=3):
    """Create Binance client with retry logic."""
    local_proxies = {
        'http': os.getenv('HTTP_PROXY'),
        'https': os.getenv('HTTPS_PROXY')
    }
    
    for attempt in range(max_retries):
        try:
            client = Client(
                BINANCE_API_KEY, 
                BINANCE_API_SECRET,
                {
                    'proxies': local_proxies,
                    'timeout': 30,
                    'verify': True
                }
            )
            # Test the connection
            client.ping()
            print("Successfully connected to Binance API")
            return client
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print("Waiting 10 seconds before retry...")
                time.sleep(10)
                os.system('sudo service tor restart')
                time.sleep(5)
            else:
                raise

# Initialize Binance client
client = create_binance_client()

# Base directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "data")
NEW_DATA_FOLDER = os.path.join(BASE_DIR, "new_data")
MERGED_FOLDER = os.path.join(BASE_DIR, "merged_data")  # New folder for merged files

def clean_folder(folder_path):
    """Clean the specified folder."""
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    print(f"Cleaned folder: {folder_path}")

def download_kaggle_dataset(dataset_slug, output_dir):
    """Download the dataset and metadata from Kaggle."""
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(dataset_slug, path=output_dir, unzip=True)
    api.dataset_metadata(dataset_slug, path=output_dir)
    print(f"Dataset and metadata downloaded to {output_dir}")

def fetch_binance_data(symbol, interval, start_date, end_date, output_file, max_retries=3):
    """Fetch historical data from Binance with retry logic."""
    for attempt in range(max_retries):
        try:
            client = create_binance_client()
            klines = client.get_historical_klines(symbol, interval, start_date, end_date)
            columns = [
                'Open time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close time', 'Quote asset volume', 'Number of trades',
                'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'
            ]
            df = pd.DataFrame(klines, columns=columns)
            # Convert timestamps to UTC datetime explicitly
            df['Open time'] = pd.to_datetime(df['Open time'], unit='ms', utc=True)
            df['Close time'] = pd.to_datetime(df['Close time'], unit='ms', utc=True)
            
            # Handle daily timeframe formatting specifically
            if interval == Client.KLINE_INTERVAL_1DAY:
                # For daily data: Open time = 00:00:00.000000, Close time = 23:59:59.999000
                df['Open time'] = df['Open time'].dt.strftime('%Y-%m-%d') + ' 00:00:00.000000 UTC'
                df['Close time'] = df['Close time'].dt.strftime('%Y-%m-%d') + ' 23:59:59.999000 UTC'
                print(f"Applied daily timeframe formatting for {len(df)} records")
            else:
                # For other timeframes: use actual timestamps
                df['Open time'] = df['Open time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]  # Remove last 3 digits for milliseconds
                df['Close time'] = df['Close time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]
                print(f"Applied standard timeframe formatting for {len(df)} records")
            
            df.to_csv(output_file, index=False)
            print(f"Fetched data saved to {output_file}")
            return
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print("Waiting 20 seconds before retry...")
                time.sleep(20)
                os.system('sudo service tor restart')
                time.sleep(5)
            else:
                raise

def merge_datasets(existing_file, new_file, output_file):
    """Merge existing and new datasets - optimized for large datasets."""
    # Read datasets
    existing_data = pd.read_csv(existing_file)
    new_data = pd.read_csv(new_file)
    
    print(f"Existing data shape: {existing_data.shape}")
    print(f"New data shape: {new_data.shape}")

    # Safety check: ensure both datasets have consistent timestamp formats
    existing_sample = str(existing_data['Open time'].iloc[0])
    new_sample = str(new_data['Open time'].iloc[0])
    
    print(f"Existing data timestamp format: {existing_sample}")
    print(f"New data timestamp format: {new_sample}")

    # Handle timezone-aware datetime parsing with improved format detection
    # For existing data (which might be in old format without explicit UTC)
    if 'UTC' in existing_sample:
        print("Existing data has explicit UTC format")
        try:
            existing_data['Open time'] = pd.to_datetime(existing_data['Open time'], format='%Y-%m-%d %H:%M:%S.%f UTC', utc=True)
            existing_data['Close time'] = pd.to_datetime(existing_data['Close time'], format='%Y-%m-%d %H:%M:%S.%f UTC', utc=True)
        except ValueError:
            # Handle case where existing data might not have microseconds
            existing_data['Open time'] = pd.to_datetime(existing_data['Open time'], utc=True)
            existing_data['Close time'] = pd.to_datetime(existing_data['Close time'], utc=True)
    else:
        print("Existing data missing explicit UTC format - assuming UTC")
        existing_data['Open time'] = pd.to_datetime(existing_data['Open time'], utc=True)
        existing_data['Close time'] = pd.to_datetime(existing_data['Close time'], utc=True)
    
    # For new data (should have explicit UTC format)
    if 'UTC' in new_sample:
        print("New data has explicit UTC format")
        try:
            new_data['Open time'] = pd.to_datetime(new_data['Open time'], format='%Y-%m-%d %H:%M:%S.%f UTC', utc=True)
            new_data['Close time'] = pd.to_datetime(new_data['Close time'], format='%Y-%m-%d %H:%M:%S.%f UTC', utc=True)
        except ValueError:
            # Handle case where new data might not have microseconds
            new_data['Open time'] = pd.to_datetime(new_data['Open time'], utc=True)
            new_data['Close time'] = pd.to_datetime(new_data['Close time'], utc=True)
    else:
        print("New data missing explicit UTC format - assuming UTC")
        new_data['Open time'] = pd.to_datetime(new_data['Open time'], utc=True)
        new_data['Close time'] = pd.to_datetime(new_data['Close time'], utc=True)

    # OPTIMIZATION: Only keep recent existing data to reduce processing time
    # Keep only data from the last 30 days to handle overlaps efficiently
    cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=30)
    new_data_start = new_data['Open time'].min()
    
    # Use the earlier of cutoff_date or new_data_start to ensure we don't miss any data
    filter_date = min(cutoff_date, new_data_start)
    
    existing_before_filter = len(existing_data)
    existing_recent = existing_data[existing_data['Open time'] >= filter_date].copy()
    existing_old = existing_data[existing_data['Open time'] < filter_date].copy()
    
    print(f"Filtered existing data: keeping {len(existing_recent)} recent records, {len(existing_old)} older records")
    
    # Merge only the recent data with new data
    merged_recent = pd.concat([existing_recent, new_data], ignore_index=True)
    duplicates_before = len(merged_recent)
    merged_recent.drop_duplicates(subset='Open time', inplace=True)
    duplicates_removed = duplicates_before - len(merged_recent)
    print(f"Removed {duplicates_removed} duplicate records from recent data")
    
    # Sort the recent merged data
    merged_recent.sort_values(by='Open time', inplace=True)
    
    # Combine old data with merged recent data
    final_data = pd.concat([existing_old, merged_recent], ignore_index=True)
    final_data.sort_values(by='Open time', inplace=True)
    
    print(f"Final dataset contains {len(final_data)} records")
    
    # Convert back to string format with UTC designation for output
    # Check if this is daily data by looking at the filename
    is_daily_data = '1d' in output_file or 'daily' in output_file.lower()
    
    if is_daily_data:
        # For daily data: standardize to 00:00:00.000000 and 23:59:59.999000
        final_data['Open time'] = final_data['Open time'].dt.strftime('%Y-%m-%d') + ' 00:00:00.000000 UTC'
        final_data['Close time'] = final_data['Close time'].dt.strftime('%Y-%m-%d') + ' 23:59:59.999000 UTC'
        print("Applied daily timeframe formatting to merged data")
    else:
        # For other timeframes: use actual timestamps
        final_data['Open time'] = final_data['Open time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC').str[:-3]
        final_data['Close time'] = final_data['Close time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f UTC').str[:-3]
        print("Applied standard timeframe formatting to merged data")
    
    final_data.to_csv(output_file, index=False)
    print(f"Merged dataset saved to {output_file}")
    print(f"Final dataset contains {len(final_data)} records")

def copy_metadata(src_folder, dest_folder):
    """Copy the metadata file to the destination folder."""
    import json
    
    # Create a comprehensive metadata file with timezone information
    metadata = {
        "title": "Bitcoin Historical Datasets 2018-2024 (UTC Timezone)",
        "id": "novandraanugrah/bitcoin-historical-datasets-2018-2024",
        "licenses": [{"name": "CC BY 4.0"}],
        "subtitle": "Historical Bitcoin price data from Binance with consistent UTC timestamps",
        "description": "This dataset contains historical Bitcoin (BTC/USDT) price data from Binance exchange with the following specifications:\n\n**Timezone Information:**\n- All timestamps are in UTC (Coordinated Universal Time)\n- Open time format: YYYY-MM-DD HH:MM:SS.ffffff UTC\n- Close time format: YYYY-MM-DD HH:MM:SS.ffffff UTC\n\n**Daily Timeframe Specific:**\n- Open time: Always shows 00:00:00.000000 UTC (start of day)\n- Close time: Always shows 23:59:59.999000 UTC (end of day)\n\n**Timeframes Available:**\n- 15-minute intervals (15m)\n- 1-hour intervals (1h) \n- 4-hour intervals (4h)\n- 1-day intervals (1d)\n\n**Data Columns:**\n- Open time: Opening timestamp in UTC\n- Open: Opening price\n- High: Highest price during period\n- Low: Lowest price during period\n- Close: Closing price\n- Volume: Trading volume\n- Close time: Closing timestamp in UTC\n- Quote asset volume: Volume in quote asset (USDT)\n- Number of trades: Number of trades during period\n- Taker buy base asset volume: Volume of taker buy orders\n- Taker buy quote asset volume: Volume of taker buy orders in quote asset\n- Ignore: Unused field\n\nData is automatically updated and maintained through automated scripts."
    }
    
    metadata_file = os.path.join(dest_folder, "dataset-metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Created comprehensive metadata file at {metadata_file}")

def upload_to_kaggle(upload_folder, dataset_slug, version_notes):
    """Upload the updated dataset to Kaggle without using the proxy."""
    # Temporarily remove proxy settings for Kaggle upload
    original_http_proxy = os.environ.pop("HTTP_PROXY", None)
    original_https_proxy = os.environ.pop("HTTPS_PROXY", None)
    try:
        api = KaggleApi()
        api.authenticate()
        api.dataset_create_version(
            folder=upload_folder,
            version_notes=version_notes,
            dir_mode=True
        )
        print("Dataset updated on Kaggle.")
    finally:
        # Restore proxy settings after upload
        if original_http_proxy:
            os.environ["HTTP_PROXY"] = original_http_proxy
        if original_https_proxy:
            os.environ["HTTPS_PROXY"] = original_https_proxy

def main():
    dataset_slug = "novandraanugrah/bitcoin-historical-datasets-2018-2024"
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(NEW_DATA_FOLDER, exist_ok=True)
    os.makedirs(MERGED_FOLDER, exist_ok=True)

    # Step 1: Clean folders (do not remove metadata until after successful upload)
    clean_folder(DATA_FOLDER)
    clean_folder(NEW_DATA_FOLDER)
    clean_folder(MERGED_FOLDER)

    # Step 2: Download Kaggle dataset and metadata into DATA_FOLDER
    download_kaggle_dataset(dataset_slug, DATA_FOLDER)

    # Step 3: Fetch new data for all timeframes
    start_date = "2025-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    timeframes = {
        "15m": Client.KLINE_INTERVAL_15MINUTE,
        "1h": Client.KLINE_INTERVAL_1HOUR,
        "4h": Client.KLINE_INTERVAL_4HOUR,
        "1d": Client.KLINE_INTERVAL_1DAY
    }

    for tf_name, tf_interval in timeframes.items():
        output_file = os.path.join(NEW_DATA_FOLDER, f"{tf_name}.csv")
        fetch_binance_data("BTCUSDT", tf_interval, start_date, end_date, output_file)

    # Step 4: Merge new data with old datasets and save the merged files in MERGED_FOLDER
    for tf_name, _ in timeframes.items():
        old_file = os.path.join(DATA_FOLDER, f"btc_{tf_name}_data_2018_to_2025.csv")
        new_file = os.path.join(NEW_DATA_FOLDER, f"{tf_name}.csv")
        merged_file = os.path.join(MERGED_FOLDER, f"btc_{tf_name}_data_2018_to_2025.csv")
        merge_datasets(old_file, new_file, merged_file)
    
    # Copy metadata file from DATA_FOLDER to MERGED_FOLDER so that Kaggle API finds it
    copy_metadata(DATA_FOLDER, MERGED_FOLDER)

    # Step 5: Upload updated datasets from MERGED_FOLDER with a retry loop until successful
    current_date = datetime.now().strftime("%B, %d %Y")
    upload_successful = False
    while not upload_successful:
        try:
            upload_to_kaggle(MERGED_FOLDER, dataset_slug, f"Update {current_date}")
            upload_successful = True
        except Exception as e:
            print(f"Upload failed: {e}. Retrying in 60 seconds...")
            time.sleep(60)

    # Step 6: Once upload is successful, clean all folders
    clean_folder(DATA_FOLDER)
    clean_folder(NEW_DATA_FOLDER)
    clean_folder(MERGED_FOLDER)

if __name__ == "__main__":
    max_attempts = 10  # Maximum number of global attempts
    attempt = 0
    while attempt < max_attempts:
        try:
            main()
            break  # Exit loop if main() succeeds
        except Exception as e:
            attempt += 1
            print(f"Global attempt {attempt}/{max_attempts} failed: {e}")
            print("Retrying in 60 seconds...")
            time.sleep(60)
    else:
        print("Max attempts reached. Exiting.")
        sys.exit(1)
