### GitHub Actions

The project includes a GitHub Actions workflow that:

- Runs automatically every Sunday at midnight (UTC)
- Can be triggered manually from the Actions tab
- Uses Tor proxy to handle API restrictions

To use GitHub Actions:

1. Add your credentials as repository secrets:
   - `KAGGLE_USERNAME`
   - `KAGGLE_KEY`
   - `BINANCE_API_KEY`
   - `BINANCE_API_SECRET`
2. Enable Actions in your repository
3. The workflow will run automatically according to schedule

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

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the CC0-1.0 License - see the dataset-metadata.json file for details.

## Acknowledgments

- Binance for providing the cryptocurrency data API
- Kaggle for hosting the dataset platform
