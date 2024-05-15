#!/usr/bin/env python3
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta

import FinNews as fn
import requests
import yfinance as yf
from bs4 import BeautifulSoup

# Setup the Ollama model
from langchain_community.llms import Ollama

models_to_test = [
    "llama3:8b-instruct-sentiment_analysis-q4_K_M",
    "llama3:8b-instruct-sentiment_analysis-q5_k_m",
    # "sentiment_llama3:8b-q8_0",
    # "sentiment_llama3:8b-fp16",
    "llama3:8b-instruct-q4_K_M",
    "llama3:8b-instruct-q5_K_M",
    # "llama3:8b-instruct-q8_0",
    # "llama3:8b-instruct-fp16",
]

sample_size = 8
ticker_symbol = "NVDA"
max_news_age = 1
max_news_items = 8

# Let's get the company name and market name for the symbol
ticker = yf.Ticker(ticker_symbol)

# Check if the symbol is a valid security (it should have a 'shortName' attribute)
company_name = ""
if "shortName" not in ticker.info:
    print("Invalid security symbol:", ticker_symbol)
else:
    company_name = ticker.info["longName"].lower()
    # Remove anything after a comma including the comma
    company_name = company_name.split(",")[0]
    to_remove = [
        "inc.",
        "incorporated",
        "corp.",
        "corporation",
        "ltd.",
        "limited",
        "co.",
        "company",
    ]
    for word in to_remove:
        company_name = company_name.replace(word, "")
    print("Company:", company_name, "(" + ticker_symbol + ")")


# The hash function used to save sentiment data to a file
def hash_url(text):
    return hashlib.md5(text.encode()).hexdigest()[0:8]


# Get the RSS feed news links for the stock


# Get the news for the stock from Yahoo Finance
yahoo_feed = fn.Yahoo(topics=["$" + ticker_symbol])
print("Getting news from Yahoo Finance...")
news_object = yahoo_feed.get_news()

# The structure of the news_object is a list of dictionaries, the following keys will be useful:
# title: a string with the title of the news
# summary: a string with a summary of the news
# link: a string with the link to the news (this is where we will scrape the news from)
# published_parsed: a datetime object with the publication date of the news

# Filter the news to only include the ones from the last n days


# Use UTC time to avoid timezone issues
now_UTC = datetime.utcnow()
cuttoff_time = now_UTC - timedelta(days=max_news_age)
for news in news_object:
    # Compute the difference between now and the publication date (time.struct_time)
    if datetime(*news["published_parsed"][:6]) < cuttoff_time:
        news_object.remove(news)

# Also limit the number of news for this example
news_object = news_object[:max_news_items]

sentiments_map = {}  # key -> sentiment json
content_map = {}  # url --> content

# Get the content of the news articles


print("Getting content from the news articles...")


def get_content(link):
    response = requests.get(link)
    if response.status_code != 200:
        # print(f"Failed to get article content from {link}")
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    content = []
    for tag in soup.find_all(["p", "h2"]):
        lower_text = tag.text.lower()
        if len(lower_text) == 0:
            continue
        if company_name in lower_text or ticker_symbol in lower_text:
            text = tag.text.strip().replace("\n", " ")
            content.append(text)
    if len(content) == 0:
        return ""
    return "… ".join(content)


for news in news_object:
    url = news["link"]

    content = ""
    # First add the summary to the content map if it doesn't end with a `?`
    lower_summary = news["summary"].lower()
    if news["summary"][-1] != "?":
        content = news["summary"]
    extra_content = get_content(url)
    if len(extra_content) > 0:
        # Append the content into the map with a separator
        content += " " + extra_content
    if len(content) > 0:
        content_map[url] = content

# JSON helper functions


def validate_json(json_data) -> tuple[bool, dict]:
    try:
        json_dict = json.loads(json_data)
        return True, json_dict
    except ValueError:
        return False, {}


def parse_json_numeric_value(json_data, key) -> float:
    try:
        value = json_data[key]
        return value
    except KeyError:
        json_str = json.dumps(json_data)
        match = re.search(r"[-+]?[0-1]\.\d+", json_str)
        if match:
            value = float(match.group())
        else:
            value = 0.0
        return value


def test_model(model_name, iteration):
    start_time = time.time()
    llm = Ollama(model=model_name, temperature=0.2)

    # If the model is a sentiment model, we don't need any special setup
    is_sentiment_model = "sentiment" in model_name
    analyze_prompt = ""
    if not is_sentiment_model:
        system_message_file = os.path.join("messages", "sentiment_system_message.txt")
        llm.system = open(system_message_file, "r").read()

        first_prompt = open(
            os.path.join("messages", "sentiment_user_first_prompt.txt")
        ).read()
        llm.invoke(first_prompt)

        # Base prompt which will we inject the content to analyze
        analyze_prompt = open(
            os.path.join("messages", "sentiment_user_message.txt")
        ).read()

    j = 0
    for url, content in content_map.items():
        if not is_sentiment_model:
            prompt = analyze_prompt.format(
                content_to_analyze=content, company_name=company_name
            )
        else:
            prompt = content

        print(f"\rIteration: {iteration + 1} item: {j + 1}/{len(content_map)}", end="")
        output = llm.invoke(prompt)
        # print(f"Raw output: {output}")

        valid, sentiment_json = validate_json(output)
        if valid:
            sentiment_json["url"] = url
            # Put the published date in as well
            published = ""
            # Find the date in the news_object
            for news in news_object:
                if news["link"] == url:
                    published = news["published"]
                    break
            sentiment_json["published"] = published
            sentiments_map[hash_url(url)] = sentiment_json
        j += 1

    # Compute the weighted average sentiment from the map
    average_sentiment = 0.0
    total_weight = 0.0
    if len(sentiments_map) > 0:
        for url, sentiment_json in sentiments_map.items():
            s_value = parse_json_numeric_value(sentiment_json, "sentiment")
            s_confidence = parse_json_numeric_value(sentiment_json, "confidence")
            # only add the sentiment if it's not 0
            if s_value != 0.0:
                average_sentiment += s_value * s_confidence
                total_weight += s_confidence
        if total_weight != 0.0:
            average_sentiment /= total_weight
            average_sentiment = round(average_sentiment, 2)

    # Prepare to insert the time taken into the sentiment map
    end_time = time.time()

    # Cache results
    # Remove illegal characters from the model name
    results_dir = os.path.join("sentiments", model_name.replace(":", "_"))
    # Make sure the directory exists for the sentiment results.
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    sentiment_file = os.path.join(results_dir, ticker_symbol + f"_{iteration}.json")
    with open(sentiment_file, "w") as file:
        data = {
            "average_sentiment": average_sentiment,
            "time_taken": round(end_time - start_time, 2),
            "sentiments": sentiments_map,
        }
        json.dump(data, file, indent=2)


for model_name in models_to_test:
    print(f"Testing model: {model_name}")
    for i in range(sample_size):
        test_model(model_name, i)
    print("")
