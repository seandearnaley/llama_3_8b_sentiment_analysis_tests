# Llama 3 8B Sentiment Analysis Tests

This repository contains code and resources for performing sentiment analysis tests using various models, specifically tailored for financial news articles. The project leverages Yahoo Finance news data, and processes it to evaluate and compare the performance of different sentiment analysis models.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Scripts](#scripts)
  - [generate_model_sentiments.py](#generate_model_sentimentspy)
  - [generate_model_comparison_report.py](#generate_model_comparison_reportpy)
  - [generate_model_metrics.py](#generate_model_metricspy)
  - [generate_heatmaps.py](#generate_heatmapspy)
- [Utils](#utils)
  - [file_utils.py](#file_utilspy)
  - [web_scraper.py](#web_scraperpy)
  - [analysis_utils.py](#analysis_utilspy)
  - [error_decorator.py](#error_decoratorpy)
  - [context.py](#contextpy)
- [License](#license)

## Installation

### Clone the Repository

First, clone the repository to your local machine:

```sh
git clone https://github.com/seandearnaley/llama_3_8b_sentiment_analysis_tests.git
cd llama_3_8b_sentiment_analysis_tests
```

### Install Dependencies

To install the necessary dependencies, ensure you have Poetry installed. Then, run the following commands:

```sh
poetry install
```

This will create a virtual environment and install all the required dependencies specified in `pyproject.toml`.

## Configuration

The project uses a YAML configuration file (`config.yaml`) to specify various parameters required for the analysis. Here is an example configuration:

```yaml
ticker_symbol: "AAPL"
max_news_age: 1
max_news_items: 5
models_to_test:
  - "model-1"
  - "model-2"
sample_size: 5
default_temperature: 0.2
context_window_size: 8192
num_tokens_to_predict: 1024
sentiment_save_folder: "sentiments"
report_output_file: "reports/model_comparisons.xlsx"
report_output_csv_file: "reports/model_metrics.csv"
heatmaps_folder: "heatmaps"
report_output_csv_folder: "reports"
comparison_pairs:
  - ["model-1", "model-2"]
```

## Usage

### generate_model_sentiments.py

This script fetches financial news articles, processes them, and tests multiple sentiment analysis models on the gathered data. To run the script, execute:

```sh
poetry run python generate_model_sentiments.py
```

### generate_model_comparison_report.py

This script compares the results from different sentiment analysis models and generates a comprehensive report in Excel and CSV formats, including statistical comparisons. To run the script, execute:

```sh
poetry run python generate_model_comparison_report.py
```

### generate_model_metrics.py

This script computes various metrics for the sentiment analysis models based on their performance and stores the results in Excel and CSV formats. To run the script, execute:

```sh
poetry run python generate_model_metrics.py
```

### generate_heatmaps.py

This script generates heatmaps for different performance metrics of the sentiment analysis models and saves them as PNG images. To run the script, execute:

```sh
poetry run python generate_heatmaps.py
```

## Utils

### file_utils.py

Contains utility functions for reading and writing files, as well as loading the configuration.

### web_scraper.py

Provides functions for web scraping news content using BeautifulSoup and handling HTTP requests.

### analysis_utils.py

Includes helper functions for processing news articles, cleaning company names, and testing models.

### error_decorator.py

Defines a decorator for handling errors gracefully across the codebase.

### context.py

Defines the `AnalysisContext` dataclass used to maintain context information throughout the analysis process.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.