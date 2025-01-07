# Macroeconomic Data Analysis

A Python package for fetching, analyzing, and storing macroeconomic data from Federal Reserve Economic Data (FRED) with AWS integration and LLM capabilities via Groq.

## Features

- **Data Fetching**: Automated retrieval of key economic indicators from FRED API
- **AWS Integration**: Secure storage and management of data in AWS S3
- **LLM Analysis**: Advanced data analysis using Groq's LLM capabilities
- **Interactive Mode**: Command-line interface for custom data queries
- **Key Indicators**: Track essential metrics including:
  - Real GDP
  - Industrial Production
  - Unemployment Rate
  - Consumer Price Index
  - Core Inflation
  - Federal Funds Rate

## Project Structure

```
macroeconomic_data/
├── mains/
│   └── fetch_federal_reserve_data.py  # Main script for data fetching
├── src/
│   └── macroeconomic_data/           # Core package functionality
├── tests/
│   ├── test_aws.py                   # AWS integration tests
│   ├── test_groq.py                  # Groq LLM tests
│   └── conftest.py                   # pytest configuration
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/macroeconomic_data.git
cd macroeconomic_data
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials and FRED API key:
- Set up AWS credentials in `~/.aws/credentials` or via environment variables
- Store your FRED API key in AWS Secrets Manager

## Usage

### Command Line Interface

1. Fetch all key economic indicators:
```bash
python mains/fetch_federal_reserve_data.py
```

2. Interactive mode for custom queries:
```bash
python mains/fetch_federal_reserve_data.py --interactive
```

### Example Queries in Interactive Mode
- "real gdp"
- "unemployment rate"
- "consumer price index"
- "federal funds rate"

## Testing

Run the test suite:
```bash
pytest tests/
```

The test suite includes:
- AWS integration tests (`test_aws.py`)
- Groq LLM functionality tests (`test_groq.py`)

## Requirements

- Python 3.8+
- AWS Account with appropriate permissions
- FRED API key
- Groq API access (for LLM capabilities)

## License

Copyright (c) 2025. All rights reserved.

This project and its contents are proprietary. No part of this project may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of the owner.

## Contributing

All changes to this project must be explicitly requested and approved by me. Please contact the owner directly for any proposed modifications or improvements.