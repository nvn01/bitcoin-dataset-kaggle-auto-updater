### GitHub Actions

The project includes a GitHub Actions workflow that:

- Runs automatically everyday at midnight (UTC)
- Updates the Kaggle dataset at https://www.kaggle.com/datasets/novandraanugrah/bitcoin-historical-datasets-2018-2024

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

## License

This project is licensed under the CC0-1.0 License - see the dataset-metadata.json file for details.

## Acknowledgments

- Binance for providing the cryptocurrency data API
- Kaggle for hosting the dataset platform
