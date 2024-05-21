import json
import logging
import os
from collections import defaultdict

import numpy as np
import pandas as pd

from utils.file_utils import load_config

CONFIG_FILE = "config.yaml"
INCLUDE_REASONING_SAMPLES = False
DECIMAL_PLACES = 2

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_model_json_files(model_path: str) -> list:
    json_data = []
    for file_name in os.listdir(model_path):
        if file_name.endswith(".json"):
            with open(os.path.join(model_path, file_name), "r") as file:
                data = json.load(file)
                json_data.append(data)
    return json_data


def extract_model_name(path: str) -> str:
    return os.path.basename(path).replace(":", "_")


def aggregate_sentiments(json_data: list) -> dict:
    aggregated_data = defaultdict(list)
    for data in json_data:
        for key, sentiment in data["sentiments"].items():
            aggregated_data[key].append(sentiment)
    return aggregated_data


def compute_metrics_per_article(aggregated_sentiments: dict) -> dict:
    metrics = defaultdict(lambda: defaultdict(list))
    for key, sentiments in aggregated_sentiments.items():
        for sentiment in sentiments:
            if sentiment["valid"]:
                metrics[key]["time_taken"].append(sentiment["time_taken"])
                metrics[key]["sentiment"].append(sentiment["sentiment"])
                metrics[key]["confidence"].append(sentiment["confidence"])
            metrics[key]["valid"].append(sentiment["valid"])

    aggregated_metrics = {}
    for key, values in metrics.items():
        valid_count = sum(values["valid"])
        total_count = len(values["valid"])

        aggregated_metrics[key] = {
            "inference_rate": round(np.mean(values["time_taken"]), DECIMAL_PLACES)
            if values["time_taken"]
            else 0,
            "valid_json_rate": round(valid_count / total_count, DECIMAL_PLACES)
            if total_count > 0
            else 0,
            "sentiment_variance": round(np.var(values["sentiment"]), DECIMAL_PLACES)
            if values["sentiment"]
            else 0,
            "mean_sentiment": round(np.mean(values["sentiment"]), DECIMAL_PLACES)
            if values["sentiment"]
            else 0,
            "mean_confidence": round(np.mean(values["confidence"]), DECIMAL_PLACES)
            if values["confidence"]
            else 0,
        }

    return aggregated_metrics


def create_xlsx_and_csvs(
    model_metrics: dict,
    output_file: str,
    output_csv_file: str,
):
    os.makedirs(os.path.dirname(output_csv_file), exist_ok=True)
    writer = pd.ExcelWriter(output_file, engine="xlsxwriter")

    # Model Details Sheet
    model_details_data = [
        {
            "Model Name": model,
            "Article Key": key,
            "Inference Rate (s)": metrics["inference_rate"],
            "Valid JSON Rate": metrics["valid_json_rate"],
            "Sentiment Variance": metrics["sentiment_variance"],
            "Mean Sentiment": metrics["mean_sentiment"],
            "Mean Confidence": metrics["mean_confidence"],
        }
        for model, model_data in model_metrics.items()
        for key, metrics in model_data.items()
    ]
    model_details_df = pd.DataFrame(model_details_data)
    model_details_df.to_excel(writer, sheet_name="Model Details", index=False)

    writer.close()

    # Save all model data to a single CSV file
    model_details_df.to_csv(output_csv_file, index=False)


def main():
    config = load_config(CONFIG_FILE)
    models_to_test = config.get("models_to_test", [])
    sentiment_save_folder = config.get("sentiment_save_folder", "sentiments")
    report_output_file = config.get("report_output_file", "reports/model_metrics.xlsx")
    report_output_csv_file = config.get(
        "report_output_csv_file", "reports/model_metrics.csv"
    )

    model_paths = [
        os.path.join(sentiment_save_folder, model.replace(":", "_"))
        for model in models_to_test
    ]

    all_data = {
        extract_model_name(path): aggregate_sentiments(load_model_json_files(path))
        for path in model_paths
    }

    logging.info("Loaded model data keys: %s", all_data.keys())

    model_metrics = {
        model: compute_metrics_per_article(sentiments)
        for model, sentiments in all_data.items()
    }

    # Save the comparison results to an Excel file and a single CSV file
    create_xlsx_and_csvs(model_metrics, report_output_file, report_output_csv_file)


if __name__ == "__main__":
    main()
