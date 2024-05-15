# Llama 3 8b Sentiment Analysis Tests

This project contains a set of scripts for generating sentiment analysis results using multiple models and comparing their performance. The primary scripts are `generate_model_sentiments.py` for gathering and processing news articles, and `generate_model_comparison_report.py` for analyzing and comparing the results.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
  - [Configuration](#configuration)
  - [Generating Sentiments](#generating-sentiments)
  - [Generating Comparison Report](#generating-comparison-report)
- [Scripts](#scripts)
  - [generate_model_sentiments.py](#generate_model_sentimentspy)
  - [generate_model_comparison_report.py](#generate_model_comparison_reportpy)
- [Utilities](#utilities)
- [Directory Structure](#directory-structure)

## Installation

To get started, you'll need to have [Poetry](https://python-poetry.org/) installed. Clone the repository and install the dependencies:

```bash
git clone <repository_url>
cd llama_3_8b_sentiment_analysis_tests
poetry install
```

## Usage

### Configuration

Configure the script by editing the `config.yaml` file:

```yaml
ticker_symbol: "AAPL"
max_news_age: 7
max_news_items: 10
models_to_test:
  - "llama3_8b-instruct-fp16"
  - "llama3_8b-instruct-q4_K_M"
  - "llama3_8b-instruct-q5_K_M"
  - "llama3_8b-instruct-q8_0"
  - "llama3_8b-instruct-sentiment_analysis-fp16"
  - "llama3_8b-instruct-sentiment_analysis-q4_K_M"
  - "llama3_8b-instruct-sentiment_analysis-q5_K_M"
  - "llama3_8b-instruct-sentiment_analysis-q8_0"
sample_size: 8
```

### Generating Sentiments

To generate sentiment analysis results for a specific company, run:

```bash
poetry run python generate_model_sentiments.py
```

This script fetches news articles, processes them, and evaluates them using different sentiment analysis models.

### Generating Comparison Report

After generating the sentiment analysis results, you can create a comparison report by running:

```bash
poetry run python generate_model_comparison_report.py
```

This script loads the sentiment analysis results, computes performance metrics, and generates a comprehensive comparison report.

## Scripts

### generate_model_sentiments.py

This script fetches news articles related to a specific company, processes the articles, and evaluates them using multiple sentiment analysis models.

- Fetches news articles using the Yahoo Finance API.
- Processes the articles to extract relevant content.
- Evaluates the content using different sentiment analysis models.
- Saves the results in JSON format.

### generate_model_comparison_report.py

This script analyzes the sentiment analysis results from multiple models and generates a comparison report.

- Loads sentiment analysis results from JSON files.
- Computes performance metrics for each model.
- Compares models using statistical tests (F-test, T-test).
- Generates an Excel report with model details and comparison results.

## Utilities

The `utils` directory contains various utility modules:

- `analysis_utils.py`: Functions for processing news articles, testing models, and analyzing content.
- `error_decorator.py`: Decorators for handling errors.
- `file_utils.py`: Functions for file operations (loading config, saving results).
- `validation_utils.py`: Functions for validating JSON output.
- `web_scraper.py`: Functions for scraping web content.

## Directory Structure

```
llama_3_8b_sentiment_analysis_tests/
├── messages/
│   ├── sentiment_system_message.txt
│   ├── sentiment_user_first_prompt.txt
│   ├── sentiment_user_message.txt
├── reports/
│   ├── model_comparisons.xlsx
│   ├── model_details.csv
│   ├── statistical_comparisons.csv
├── utils/
│   ├── analysis_utils.py
│   ├── error_decorator.py
│   ├── file_utils.py
│   ├── validation_utils.py
│   ├── web_scraper.py
├── .DS_Store
├── config.yaml
├── generate_model_comparison_report.py
├── generate_model_sentiments.py
├── poetry.lock
├── pyproject.toml
├── README.md
```


### Interpreting Sentiment Analysis Model Comparison Results

When working with sentiment analysis models, understanding their performance and comparing different models is crucial. Here’s a simple guide to help you interpret the results from our analysis, which includes model details, performance metrics, and statistical comparisons.

#### Model Details

1. **Model Name**: This indicates the specific model used (e.g., `llama3_8b-instruct-fp16`).
2. **Quantization Level**: This tells you the precision level used in the model (e.g., `q4`, `q5`, `fp16`). Lower levels like `q4` and `q5` use less memory and can be faster but might be less accurate.

#### Performance Metrics

1. **Rate (sec/sample)**: This measures how fast the model processes each sample. Lower numbers mean faster performance.
2. **Valid JSON Response Rate**: This is the percentage of times the model successfully returned valid results. Higher percentages indicate better reliability.
3. **Variance**: This shows how much the sentiment scores vary. High variance means the scores are spread out widely, while low variance means they are more consistent.
4. **Mean Sentiment Score**: This is the average sentiment score across all samples, indicating the general sentiment detected (positive, negative, or neutral).
5. **Mean Confidence**: This is the average confidence level of the sentiment predictions. Higher values indicate the model is more certain about its predictions.
6. **Reasoning**: This provides sample explanations from the model, showing why it predicted a certain sentiment. It helps understand the model's decision-making process.

#### Statistical Comparisons

We use statistical tests to compare fine-tuned models (designed specifically for sentiment analysis) against their general-purpose counterparts.

1. **F-statistic and P-value (Variance)**: These values come from the F-test, which compares the variance in sentiment scores between two models. A significant p-value (typically less than 0.05) means there is a meaningful difference in how consistent the models are.
2. **T-statistic and P-value (Mean)**: These values come from the t-test, which compares the average sentiment scores between two models. A significant p-value (typically less than 0.05) indicates a meaningful difference in the average sentiments detected by the models.

#### How to Interpret the Results

- **Inference Speed**: Faster models (lower Rate) are generally preferable, especially for real-time applications.
- **Reliability**: Models with higher Valid JSON Response Rates are more dependable.
- **Consistency**: Low Variance is often better, indicating the model's predictions are stable.
- **Sentiment and Confidence**: Higher Mean Sentiment Scores and Mean Confidence Scores are desirable, showing the model detects clear sentiment and is confident about its predictions.
- **Statistical Significance**: If the p-values for variance and mean comparisons are below 0.05, it suggests there are significant differences between the models. This helps you decide whether a specialized (fine-tuned) model offers real benefits over a general-purpose one.

### Example

Imagine comparing `llama3_8b-instruct-fp16` with `llama3_8b-instruct-sentiment_analysis-fp16`:
- **Rate**: If the sentiment analysis model is faster, it’s better for real-time needs.
- **Valid JSON Response Rate**: If higher, it means fewer errors.
- **Variance**: If lower, the model’s predictions are more consistent.
- **Mean Sentiment Score**: Higher score indicates a stronger overall sentiment detection.
- **Mean Confidence**: Higher value means the model is more certain about its predictions.
- **Statistical Tests**: If p-values are significant, the differences in performance metrics are meaningful.

By understanding these metrics and comparisons, even beginners can make informed decisions about which sentiment analysis models to use based on their specific needs and contexts.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss improvements or bugs.
