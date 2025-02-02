### GitHub Actions

The project includes a GitHub Actions workflow that:

- Runs automatically everyday at midnight (UTC)

## Dataset Structure

The script maintains four CSV files with different timeframes:

- `btc_15m_data_2018_to_2025.csv` (15-minute intervals)
- `btc_1h_data_2018_to_2025.csv` (1-hour intervals)
- `btc_4h_data_2018_to_2025.csv` (4-hour intervals)
- `btc_1d_data_2018_to_2025.csv` (daily intervals)

Each file contains the following columns:

- Open time
- Open
- High
- Low
- Close
- Volume
- Close time
- Quote asset volume
- Number of trades
- Taker buy base asset volume
- Taker buy quote asset volume

## Automated Daily Updates

This dataset is automatically updated every day using a custom Python program.  
The source code for the update script is available on GitHub:  
🔗 [Bitcoin Dataset Kaggle Auto Updater](https://github.com/nvn01/bitcoin-dataset-kaggle-auto-updater)

## License

This project is licensed under the CC0-1.0 License - see the dataset-metadata.json file for details.

## Acknowledgments

- Binance for providing the cryptocurrency data API
- Kaggle for hosting the dataset platform
