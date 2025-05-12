from http.client import responses
from time import strftime
from datetime import datetime
from settings import *
import os
import requests
from requests.exceptions import RequestException
import pandas as pd
from storage import DBStorage
from urllib.parse import quote_plus
from gemini_integration import GeminiEnhancer

# Initialize the Gemini enhancer
gemini = GeminiEnhancer()


def search_api(query, country=None, pages=int(RESULT_COUNT / 10)):
    """
    Search using the Google Custom Search API with optional country filtering.

    Args:
        query (str): The search query
        country (str, optional): Two-letter country code (ISO 3166-1 alpha-2)
        pages (int): Number of pages to retrieve

    Returns:
        DataFrame: Search results
    """
    results = []
    for i in range(0, pages):
        start = i * 10 + 1

        # Base URL
        url = SEARCH_URL.format(
            key=SEARCH_KEY,
            cx=SEARCH_ID,
            query=quote_plus(query),
            start=start
        )

        # Add country restriction if provided
        if country and len(country) == 2:
            url += f"&cr=country{country.upper()}"

        try:
            response = requests.get(url)
            data = response.json()

            # Check if 'items' exists in the response
            if 'items' in data:
                results += data['items']
            else:
                print(f"No items found in API response for page {i + 1}")
        except Exception as e:
            print(f"Error in search API call: {e}")

    # If we have results, convert to DataFrame
    if results:
        res_df = pd.DataFrame.from_dict(results)
        res_df["rank"] = list(range(1, res_df.shape[0] + 1))
        res_df = res_df[["link", "rank", "snippet", "title"]]
        return res_df
    else:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=["link", "rank", "snippet", "title"])


def scrape_page(links):
    """
    Scrape HTML content for each link.

    Args:
        links (list): List of URLs to scrape

    Returns:
        list: HTML content for each link
    """
    html = []
    for link in links:
        try:
            data = requests.get(link, timeout=5)
            html.append(data.text)
        except RequestException:
            html.append("")
    return html


def search(query, country=None):
    """
    Enhanced search function with Gemini integration and country filtering.

    Args:
        query (str): Original user query
        country (str, optional): Two-letter country code for location-specific results

    Returns:
        DataFrame: Enhanced and ranked search results
    """
    columns = ["query", "rank", "link", "title", "snippet", "html", "created"]
    storage = DBStorage()

    # Step 1: Query Expansion with Gemini
    try:
        # Check if Gemini API key is available
        if os.getenv("GEMINI_API_KEY"):
            expanded_query = gemini.expand_query(query)
            print(f"Original query: {query}")
            print(f"Expanded query: {expanded_query}")
        else:
            expanded_query = query
            print(f"No Gemini API key found. Using original query: {query}")
    except Exception as e:
        print(f"Error in query expansion: {e}")
        expanded_query = query  # Fallback to original query

    # Create a unique identifier for this query + country combination
    query_id = query
    if country:
        query_id = f"{query}__country_{country}"

    # Check for stored results with this query ID
    stored_results = storage.query_results(query_id)
    if stored_results.shape[0] > 0:
        stored_results["created"] = pd.to_datetime(stored_results["created"])

        # For stored results, we still enhance with semantic ranking if API key is available
        if os.getenv("GEMINI_API_KEY"):
            try:
                stored_results = gemini.rank_results_semantically(query, stored_results)
                stored_results = gemini.filter_content(stored_results)
                stored_results = stored_results.sort_values("rank", ascending=True)
            except Exception as e:
                print(f"Error enhancing stored results: {e}")

        return stored_results[columns]

    # Get fresh search results using expanded query and country parameter
    results = search_api(expanded_query, country=country)

    # If no results found, try with original query
    if results.empty and expanded_query != query:
        results = search_api(query, country=country)

    # If still no results, return empty DataFrame
    if results.empty:
        return pd.DataFrame(columns=columns)

    # Get HTML content
    results["html"] = scrape_page(results["link"])
    results = results[results["html"].str.len() > 0].copy()

    # Add query and timestamp - use the query_id to store country information
    results["query"] = query_id
    results["created"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Step 5: Semantic Ranking + Filtering + Summarization with Gemini (if API key is available)
    if os.getenv("GEMINI_API_KEY"):
        try:
            # Enhanced semantic ranking
            results = gemini.rank_results_semantically(query, results)

            # Content filtering
            results = gemini.filter_content(results)

            # Generate improved snippets
            results = gemini.generate_improved_snippets(results)

            # Sort by the enhanced rank
            results = results.sort_values("rank", ascending=True)
        except Exception as e:
            print(f"Error in semantic enhancement: {e}")

    # Select columns and store results
    results = results[columns]
    results.apply(lambda x: storage.insert_row(x), axis=1)

    return results