import os
import sys
import time
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

# Configure proxy settings
proxies = {
    'http': os.getenv('HTTP_PROXY'),
    'https': os.getenv('HTTPS_PROXY')
}

def create_binance_client(max_retries=3):
    """Create Binance client with retry logic."""
    proxies = {
        'http': os.getenv('HTTP_PROXY'),
        'https': os.getenv('HTTPS_PROXY')
    }
    
    for attempt in range(max_retries):
        try:
            client = Client(
                BINANCE_API_KEY, 
                BINANCE_API_SECRET,
                {
                    'proxies': proxies,
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
                # Restart Tor service to get a new IP
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
            df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
            df['Close time'] = pd.to_datetime(df['Close time'], unit='ms')
            df.to_csv(output_file, index=False)
            print(f"Fetched data saved to {output_file}")
            return
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print("Waiting 20 seconds before retry...")
                time.sleep(20)
                # Restart Tor service to get a new IP
                os.system('sudo service tor restart')
                time.sleep(5)
            else:
                raise

def merge_datasets(existing_file, new_file, output_file):
    """Merge existing and new datasets."""
    existing_data = pd.read_csv(existing_file)
    new_data = pd.read_csv(new_file)

    # Ensure Open time and Close time are datetime
    existing_data['Open time'] = pd.to_datetime(existing_data['Open time'])
    new_data['Open time'] = pd.to_datetime(new_data['Open time'])

    merged_data = pd.concat([existing_data, new_data])
    merged_data.drop_duplicates(subset='Open time', inplace=True)
    merged_data.sort_values(by='Open time', inplace=True)
    merged_data.to_csv(output_file, index=False)
    print(f"Merged dataset saved to {output_file}")

def upload_to_kaggle(output_dir, dataset_slug, version_notes):
    """Upload the updated dataset to Kaggle."""
    api = KaggleApi()
    api.authenticate()
    api.dataset_create_version(
        folder=output_dir,  # Or path=output_dir
        version_notes=version_notes,
        dir_mode=True
    )
    print("Dataset updated on Kaggle.")

def main():
    dataset_slug = "novandraanugrah/bitcoin-historical-datasets-2018-2024"
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(NEW_DATA_FOLDER, exist_ok=True)

    # Step 1: Clean folders
    clean_folder(DATA_FOLDER)
    clean_folder(NEW_DATA_FOLDER)

    # Step 2: Download Kaggle dataset and metadata
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

    # Step 4: Merge new data with old datasets
    for tf_name, _ in timeframes.items():
        old_file = os.path.join(DATA_FOLDER, f"btc_{tf_name}_data_2018_to_2025.csv")
        new_file = os.path.join(NEW_DATA_FOLDER, f"{tf_name}.csv")
        merged_file = old_file  # Output file matches the original Kaggle dataset
        merge_datasets(old_file, new_file, merged_file)

    # Step 5: Upload updated datasets to Kaggle
    current_date = datetime.now().strftime("%B, %d %Y")
    upload_to_kaggle(DATA_FOLDER, dataset_slug, f"Update {current_date}")

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
