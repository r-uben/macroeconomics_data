# Macroeconomic Data Fetcher

A Python tool for fetching and analyzing macroeconomic data from multiple sources using natural language queries.

## Features

- **Multi-Source Data Integration**:
  - Historical data from Federal Reserve Economic Data (FRED)
  - Forecast data from Federal Reserve Greenbook/Tealbook
  - Intelligent source selection using LLM

- **Natural Language Interface**:
  - Query data using plain English
  - Automatic source selection based on query intent
  - Interactive mode for FRED queries

- **AWS Integration**:
  - Secure API key management via AWS Secrets Manager
  - Data storage in S3 buckets
  - Automated updates and versioning

- **LLM-Powered Analysis**:
  - Query interpretation using Groq API
  - Smart variable matching
  - Automatic source selection

## Project Structure

```
macroeconomic_data/
├── mains/
│   ├── fetch_data.py         # Main unified fetcher
│   ├── fetch_federal_reserve_data.py
│   └── fetch_greenbook_data.py
├── src/
│   └── macroeconomic_data/
│       ├── fred/            # FRED-specific components
│       │   ├── core/
│       │   ├── services/
│       │   └── utils/
│       ├── greenbook/       # Greenbook-specific components
│       │   ├── core/
│       │   ├── services/
│       │   └── utils/
│       └── aws/             # AWS utilities
├── tests/
└── data/                    # Local data storage
    ├── fred/               # FRED data by variable
    └── green_book/         # Greenbook data by variable
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```

3. Configure AWS credentials:
   - Set up AWS credentials in `~/.aws/credentials`
   - Ensure you have access to the required AWS Secrets Manager secrets:
     - `FRED_API_KEY`
     - `GROQ_API_KEY`

## Usage

### Unified Data Fetcher

The main command for fetching data from any source:

```bash
poetry run fetch-data "your query here"
```

Examples:
- For Greenbook forecasts:
  ```bash
  poetry run fetch-data "greenbook projections for real gdp"
  poetry run fetch-data "what are the fed's forecasts for unemployment"
  ```

- For FRED historical data:
  ```bash
  poetry run fetch-data "historical real gdp data"
  poetry run fetch-data "what's the current unemployment rate"
  ```

The fetcher will:
1. Analyze your query using LLM
2. Select the appropriate data source
3. Fetch the requested data
4. Save it in the corresponding directory (`data/fred/` or `data/green_book/`)

### Source-Specific Fetchers

You can also use source-specific fetchers directly:

#### FRED Data

```bash
# Interactive mode
poetry run fetch-fred-data -i

# Fetch all key indicators
poetry run fetch-fred-data
```

#### Greenbook Data

```bash
# Fetch specific variable
poetry run fetch-greenbook-data --query "real gdp"

# Check for updates
poetry run fetch-greenbook-data --check-updates
```

## Data Organization

Data is organized by source and variable:

- FRED data: `data/fred/<variable_name>/`
  - `data.csv`: Time series data
  - `metadata.txt`: Variable information

- Greenbook data: `data/green_book/<variable_code>/`
  - `data.csv`: Historical and forecast data
  - `metadata.txt`: Variable information

## Requirements

- Python 3.9+
- AWS account with access to:
  - Secrets Manager (for API keys)
  - S3 (for Greenbook data storage)
- FRED API access
- Groq API access

## License

Copyright (c) 2024. All rights reserved.

This project is proprietary and may not be reproduced or distributed without explicit permission.

## Contributing

All changes must be explicitly requested and approved by the project owner. Please contact the owner for any proposed modifications.

## Usage Examples

### Using the Unified Data Fetcher

You can fetch data using natural language queries:

```bash
poetry run fetch-data "greenbook gdp price index"
```

Example interaction:
```
🔍 Processing query: greenbook gdp price index

================================================================================

🤔 Analyzing your query...
📊 Selected Data Source: GREENBOOK
💡 Reasoning: The user mentioned 'greenbook' in the query, which indicates they are likely looking for forecast or projection data.

================================================================================

📥 Fetching Greenbook projections...

Multiple matches found. Please choose one:
1. gdp.price_gdp (The GDP price index is also known as the GDP deflator, which measures the price level of all new, domestically produced final goods and services in an economy. It is very similar to the Consumer Price Index (CPI) and Producer Price Index (PPI), but the GDP deflator includes a broader range of goods and services. The 'gdp.price_gdp' variable measures GDP price inflation on a quarterly basis, annualized as a percentage point.)
2. cpi.headline (The Consumer Price Index (CPI) is a measure of the average change over time in the prices paid by urban consumers for a market basket of consumer goods and services. The 'cpi.headline' variable measures headline CPI inflation on a quarterly basis, annualized as a percentage point. While not exactly the GDP price index, it is a widely used inflation indicator that can provide context for price changes in the economy.)
3. pce.headline (The Personal Consumption Expenditures (PCE) Price Index is a measure of the prices that people living in the United States, regardless of where they were born or where they live, pay for goods and services. The 'pce.headline' variable measures headline PCE inflation on a quarterly basis, annualized as a percentage point. While not exactly the GDP price index, it can provide context for price changes in the economy.)

Enter number (0 to cancel): 1

================================================================================

✅ Data fetched and saved successfully!
```

The tool will:
1. Analyze your query to determine the appropriate data source
2. If multiple relevant variables are found, provide detailed explanations to help you choose
3. Fetch and save the selected data
4. Store both the data and its metadata for future reference