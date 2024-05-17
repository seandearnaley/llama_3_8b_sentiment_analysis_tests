import json
import logging
import os

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind
from scipy.stats._stats_py import TtestResult

from utils.file_utils import (
    load_config,
)

CONFIG_FILE = "config.yaml"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_json_files(model_path: str) -> list:
    json_data = []
    for file_name in os.listdir(model_path):
        if file_name.endswith(".json"):
            with open(os.path.join(model_path, file_name), "r") as file:
                data = json.load(file)
                json_data.append(data)
    return json_data


def extract_sentiments(json_data: list) -> list:
    sentiments = []
    for data in json_data:
        sentiments.extend(data["sentiments"].values())
    return sentiments


def extract_model_name(path: str) -> str:
    return os.path.basename(path)


def compute_metrics(sentiments: list, report_example_sample_size: int) -> dict:
    valid_sentiments = [s for s in sentiments if s["valid"]]
    rate = np.mean([s["time_taken"] for s in valid_sentiments])
    valid_json_rate = len(valid_sentiments) / len(sentiments)
    sentiment_scores = [s["sentiment"] for s in valid_sentiments]
    confidence_scores = [s["confidence"] for s in valid_sentiments]
    variance = np.var(sentiment_scores)
    mean_sentiment = np.mean(sentiment_scores)
    mean_confidence = np.mean(confidence_scores)
    reasoning_samples = [
        s["reasoning"] for s in valid_sentiments[:report_example_sample_size]
    ]  # Take the first n reasonings as sample / report_example_sample_size
    return {
        "rate": rate,
        "valid_json_rate": valid_json_rate,
        "variance": variance,
        "mean_sentiment": mean_sentiment,
        "mean_confidence": mean_confidence,
        "reasoning_samples": reasoning_samples,
    }


def compare_models(model1_sentiments: list, model2_sentiments: list) -> dict:
    sentiments1 = [s["sentiment"] for s in model1_sentiments if "sentiment" in s]
    sentiments2 = [s["sentiment"] for s in model2_sentiments if "sentiment" in s]
    variance_test = f_oneway(sentiments1, sentiments2)
    mean_test: TtestResult = ttest_ind(sentiments1, sentiments2)

    return {
        "f_statistic": variance_test.statistic,
        "f_p_value": variance_test.pvalue,
        "t_statistic": mean_test.statistic,  # type: ignore
        "t_p_value": mean_test.pvalue,  # type: ignore
    }


def create_spreadsheet(
    model_metrics: dict,
    comparisons: dict,
    output_file: str,
    output_csv_folder: str,
):
    os.makedirs(output_csv_folder, exist_ok=True)
    writer = pd.ExcelWriter(output_file, engine="xlsxwriter")

    # Model Details Sheet
    model_details = pd.DataFrame(
        [
            {"Model Name": model, "Quantization Level": model.split("-")[-1], **metrics}
            for model, metrics in model_metrics.items()
        ]
    )
    model_details.to_excel(writer, sheet_name="Model Details", index=False)
    model_details.to_csv(
        os.path.join(output_csv_folder, "model_details.csv"), index=False
    )

    # Statistical Comparisons Sheet
    comparison_results = pd.DataFrame(
        [
            {"Comparison": comparison, **stats}
            for comparison, stats in comparisons.items()
        ]
    )
    comparison_results.to_excel(
        writer, sheet_name="Statistical Comparisons", index=False
    )
    comparison_results.to_csv(
        os.path.join(output_csv_folder, "statistical_comparisons.csv"), index=False
    )

    writer.close()


def main():
    config = load_config(CONFIG_FILE)
    models_to_test = config.get("models_to_test", [])
    comparison_pairs = config.get("comparison_pairs", [])
    sentiment_save_folder = config.get("sentiment_save_folder", "sentiments")
    report_output_file = config.get(
        "report_output_file", "reports/model_comparisons.xlsx"
    )
    report_output_csv_folder = config.get("report_output_csv_folder", "reports")
    report_example_sample_size = config.get("report_example_sample_size", 5)

    # Prepend sentiment_save_folder to each model path
    model_paths = [
        os.path.join(sentiment_save_folder, model.replace(":", "_"))
        for model in models_to_test
    ]

    # Load all data
    all_data = {
        extract_model_name(path): extract_sentiments(load_json_files(path))
        for path in model_paths
    }

    # Debugging: Print all_data keys
    logging.info("Loaded model data keys:", all_data.keys())

    # Compute metrics for all models
    model_metrics = {
        model: compute_metrics(sentiments, report_example_sample_size)
        for model, sentiments in all_data.items()
    }

    # Perform comparisons
    comparisons = {}
    for m1, m2 in comparison_pairs:
        # Debugging: Print models being compared
        logging.info(f"Comparing {m1} with {m2}")
        try:
            comparisons[f"{m1} vs {m2}"] = compare_models(all_data[m1], all_data[m2])
        except KeyError as e:
            logging.info(f"KeyError: {e} - One of the models not found in loaded data.")

    # Create spreadsheet
    create_spreadsheet(
        model_metrics, comparisons, report_output_file, report_output_csv_folder
    )


if __name__ == "__main__":
    main()
