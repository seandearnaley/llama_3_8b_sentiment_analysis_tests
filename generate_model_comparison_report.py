import os

import pandas as pd
import yaml


def load_csv_data(csv_file: str) -> pd.DataFrame:
    data = pd.read_csv(csv_file)
    # Normalize model names in the DataFrame
    data["Model Name"] = data["Model Name"].str.replace("-", "_").str.lower()
    return data


def load_config(config_file: str) -> dict:
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)
    # Normalize model names in the configuration
    for pair in config["comparison_pairs"]:
        pair[0] = pair[0].replace("-", "_").lower()
        pair[1] = pair[1].replace("-", "_").lower()
    return config


def compare_models(data: pd.DataFrame, comparison_pairs: list) -> pd.DataFrame:
    comparison_data = []
    article_keys = data["Article Key"].unique()

    for article_key in article_keys:
        article_data = data[data["Article Key"] == article_key]
        for model1, model2 in comparison_pairs:
            model1_data = article_data[article_data["Model Name"] == model1]
            model2_data = article_data[article_data["Model Name"] == model2]

            # Debugging statements
            print(f"Comparing {model1} and {model2} for Article Key {article_key}")

            comparison_data.append(
                {
                    "Article Key": article_key,
                    "Model 1": model1,
                    "Model 2": model2,
                    "Model 1 Mean Sentiment": model1_data["Mean Sentiment"].mean(),
                    "Model 2 Mean Sentiment": model2_data["Mean Sentiment"].mean(),
                    "Model 1 Variance": model1_data["Sentiment Variance"].mean(),
                    "Model 2 Variance": model2_data["Sentiment Variance"].mean(),
                    "Model 1 Mean Confidence": model1_data["Mean Confidence"].mean(),
                    "Model 2 Mean Confidence": model2_data["Mean Confidence"].mean(),
                    "Model 1 Time Taken": model1_data["Inference Rate (s)"].mean(),
                    "Model 2 Time Taken": model2_data["Inference Rate (s)"].mean(),
                }
            )

    return pd.DataFrame(comparison_data)


def create_comparison_report(
    comparison_df: pd.DataFrame, output_xlsx: str, output_csv: str
):
    os.makedirs(os.path.dirname(output_xlsx), exist_ok=True)
    writer = pd.ExcelWriter(output_xlsx, engine="xlsxwriter")

    comparison_df.to_excel(writer, sheet_name="Model Comparison", index=False)
    writer.close()

    comparison_df.to_csv(output_csv, index=False)


def main():
    config_file = "config.yaml"
    config = load_config(config_file)

    input_csv_file = "reports/model_metrics.csv"
    output_xlsx_file = config["report_output_file"]
    output_csv_file = os.path.join(
        config["report_output_csv_folder"], "model_comparison.csv"
    )

    data = load_csv_data(input_csv_file)
    comparison_df = compare_models(data, config["comparison_pairs"])
    create_comparison_report(comparison_df, output_xlsx_file, output_csv_file)


if __name__ == "__main__":
    main()
