import json
import os

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, ttest_ind
from scipy.stats._stats_py import TtestResult


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


def compute_metrics(sentiments: list) -> dict:
    valid_sentiments = [s for s in sentiments if s["valid"]]
    rate = np.mean([s["time_taken"] for s in valid_sentiments])
    valid_json_rate = len(valid_sentiments) / len(sentiments)
    sentiment_scores = [s["sentiment"] for s in valid_sentiments]
    confidence_scores = [s["confidence"] for s in valid_sentiments]
    variance = np.var(sentiment_scores)
    mean_sentiment = np.mean(sentiment_scores)
    mean_confidence = np.mean(confidence_scores)
    reasoning_samples = [
        s["reasoning"] for s in valid_sentiments[:5]
    ]  # Take the first 5 reasonings as sample
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

    # Debugging information
    print(f"mean_test type: {type(mean_test)}")
    print(f"mean_test: {mean_test}")

    return {
        "f_statistic": variance_test.statistic,
        "f_p_value": variance_test.pvalue,
        "t_statistic": mean_test.statistic,  # type: ignore
        "t_p_value": mean_test.pvalue,  # type: ignore
    }


def create_spreadsheet(
    model_metrics: dict, comparisons: dict, output_file: str = "model_comparisons.xlsx"
):
    writer = pd.ExcelWriter(output_file, engine="xlsxwriter")

    # Model Details Sheet
    model_details = pd.DataFrame(
        [
            {"Model Name": model, "Quantization Level": model.split("-")[-1], **metrics}
            for model, metrics in model_metrics.items()
        ]
    )
    model_details.to_excel(writer, sheet_name="Model Details", index=False)
    model_details.to_csv("model_details.csv", index=False)  # Output to CSV

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
        "statistical_comparisons.csv", index=False
    )  # Output to CSV

    writer.close()  # Use close() method instead of save() to properly write and close the file


# Define paths to your model directories
model_dirs = [
    "sentiments/llama3_8b-instruct-fp16",
    "sentiments/llama3_8b-instruct-q4_K_M",
    "sentiments/llama3_8b-instruct-q5_K_M",
    "sentiments/llama3_8b-instruct-q8_0",
    "sentiments/llama3_8b-instruct-sentiment_analysis-fp16",
    "sentiments/llama3_8b-instruct-sentiment_analysis-q4_K_M",
    "sentiments/llama3_8b-instruct-sentiment_analysis-q5_K_M",
    "sentiments/llama3_8b-instruct-sentiment_analysis-q8_0",
]

# Load all data
all_data = {
    extract_model_name(path): extract_sentiments(load_json_files(path))
    for path in model_dirs
}

# Compute metrics for all models
model_metrics = {
    model: compute_metrics(sentiments) for model, sentiments in all_data.items()
}

# Define pairs to compare
comparison_pairs = [
    ("llama3_8b-instruct-fp16", "llama3_8b-instruct-sentiment_analysis-fp16"),
    ("llama3_8b-instruct-q4_K_M", "llama3_8b-instruct-sentiment_analysis-q4_K_M"),
    ("llama3_8b-instruct-q5_K_M", "llama3_8b-instruct-sentiment_analysis-q5_K_M"),
    ("llama3_8b-instruct-q8_0", "llama3_8b-instruct-sentiment_analysis-q8_0"),
]

# Perform comparisons
comparisons = {
    f"{m1} vs {m2}": compare_models(all_data[m1], all_data[m2])
    for m1, m2 in comparison_pairs
}

# Create spreadsheet
create_spreadsheet(model_metrics, comparisons)