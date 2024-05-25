import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils.file_utils import load_config

CONFIG_FILE = "config.yaml"


# Function to plot and save heatmap
def plot_heatmap(data, title, value_label, cmap, padding, filename):
    plt.figure(figsize=(20, 10))
    sns.heatmap(
        data,
        annot=True,
        cmap=cmap,
        cbar_kws={"label": value_label},
        annot_kws={"size": 10},
        fmt=".2f",
    )
    plt.title(title, fontsize=14)
    plt.xlabel("Model Name", fontsize=12)
    plt.ylabel("Article Key", fontsize=12)
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    plt.tight_layout(pad=padding)
    plt.savefig(filename)
    plt.close()


def main():
    config = load_config(CONFIG_FILE)

    report_output_csv_file = config.get("report_output_csv_file")

    if not report_output_csv_file:
        raise ValueError("No report output file specified in the config.")

    heatmaps_folder = config.get("heatmaps_folder")

    if not heatmaps_folder:
        raise ValueError("No heatmaps folder specified in the config.")

    # Create heatmaps folder if not exists
    os.makedirs(heatmaps_folder, exist_ok=True)

    # Load the CSV/ report output file
    df = pd.read_csv(report_output_csv_file)

    # Inference Rate (s)
    inference_rate_pivot = df.pivot(
        index="Article Key", columns="Model Name", values="Inference Rate (s)"
    )
    inference_rate_pivot.loc["Mean"] = inference_rate_pivot.mean()
    plot_heatmap(
        inference_rate_pivot,
        "Inference Rate (s) Heatmap",
        "Inference Rate (s)",
        "coolwarm",
        5,
        os.path.join(heatmaps_folder, "inference_rate_heatmap.png"),
    )

    # Valid JSON Rate
    valid_json_pivot = df.pivot(
        index="Article Key", columns="Model Name", values="Valid JSON Rate"
    )
    valid_json_pivot.loc["Mean"] = valid_json_pivot.mean()
    plot_heatmap(
        valid_json_pivot,
        "Valid JSON Rate Heatmap",
        "Valid JSON Rate",
        "coolwarm_r",
        5,
        os.path.join(heatmaps_folder, "valid_json_rate_heatmap.png"),
    )

    # Sentiment Variance
    sentiment_variance_pivot = df.pivot(
        index="Article Key", columns="Model Name", values="Sentiment Variance"
    )
    sentiment_variance_pivot.loc["Mean"] = sentiment_variance_pivot.mean()
    plot_heatmap(
        sentiment_variance_pivot,
        "Sentiment Variance Heatmap",
        "Sentiment Variance",
        "coolwarm",
        5,
        os.path.join(heatmaps_folder, "sentiment_variance_heatmap.png"),
    )

    # Mean Sentiment
    mean_sentiment_pivot = df.pivot(
        index="Article Key", columns="Model Name", values="Mean Sentiment"
    )
    mean_sentiment_pivot.loc["Mean"] = mean_sentiment_pivot.mean()
    plot_heatmap(
        mean_sentiment_pivot,
        "Mean Sentiment Heatmap",
        "Mean Sentiment",
        "coolwarm",
        5,
        os.path.join(heatmaps_folder, "mean_sentiment_heatmap.png"),
    )

    # Mean Confidence
    mean_confidence_pivot = df.pivot(
        index="Article Key", columns="Model Name", values="Mean Confidence"
    )
    mean_confidence_pivot.loc["Mean"] = mean_confidence_pivot.mean()
    plot_heatmap(
        mean_confidence_pivot,
        "Mean Confidence Heatmap",
        "Mean Confidence",
        "coolwarm",
        5,
        os.path.join(heatmaps_folder, "mean_confidence_heatmap.png"),
    )


if __name__ == "__main__":
    main()
