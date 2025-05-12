import google.generativeai as genai
from google.ai import generativelanguage as glm
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in .env file. Gemini features will not work.")
else:
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiEnhancer:
    def __init__(self):
        """Initialize the Gemini model for various search enhancements."""
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def expand_query(self, query, country=None):
        """
        Expand the user query to improve search results by adding relevant terms.
        Includes country context if provided.

        Args:
            query (str): Original user query
            country (str, optional): Two-letter country code for location context

        Returns:
            str: Expanded query with additional relevant terms
        """
        country_context = ""
        if country and len(country) == 2:
            country_context = f"The searcher is located in country with code {country.upper()}. "
            country_context += "Optimize the query expansion for relevance to this location when appropriate."

        prompt = f"""
        You are an expert search query enhancer. Your task is to expand the following search query 
        to improve search results. Add relevant terms that would help find the most accurate information.
        Keep the expanded query concise and focused on the original intent.
        {country_context}

        Original query: {query}

        Enhanced query: 
        """

        response = self.model.generate_content(prompt)
        expanded_query = response.text.strip()

        # Ensure we don't get an overly complex query
        if len(expanded_query.split()) > 15:
            # If too long, just use original query with minimal expansion
            words = expanded_query.split()
            expanded_query = " ".join(words[:15])

        return expanded_query

    def rank_results_semantically(self, query, results_df):
        """
        Rank search results based on semantic relevance to the query.

        Args:
            query (str): User query
            results_df (DataFrame): DataFrame containing search results

        Returns:
            DataFrame: Results with semantic relevance scores
        """
        # Create a copy to avoid modifying the original
        enhanced_df = results_df.copy()

        # Add a semantic_score column
        enhanced_df['semantic_score'] = 0.0

        # Process in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(enhanced_df), batch_size):
            batch = enhanced_df.iloc[i:i + batch_size]

            for idx, row in batch.iterrows():
                # Create a relevance assessment prompt
                prompt = f"""
                Query: {query}

                Document Title: {row['title']}
                Document Snippet: {row['snippet']}

                On a scale from 0.0 to 10.0, how relevant is this document to the query?
                Provide only a numeric score without any explanation.
                """

                try:
                    response = self.model.generate_content(prompt)
                    score_text = response.text.strip()
                    # Extract numeric value from response
                    try:
                        score = float(score_text)
                        # Ensure score is within bounds
                        score = max(0.0, min(10.0, score))
                        enhanced_df.at[idx, 'semantic_score'] = score
                    except ValueError:
                        # If we can't parse a number, use a default score
                        enhanced_df.at[idx, 'semantic_score'] = 5.0
                except Exception as e:
                    print(f"Error scoring result {idx}: {e}")
                    enhanced_df.at[idx, 'semantic_score'] = 5.0

        # Adjust the rank based on semantic score
        # The lower the rank number, the better (rank 1 is best)
        # So we subtract the semantic score from the current rank
        enhanced_df['rank'] = enhanced_df['rank'] - (enhanced_df['semantic_score'] / 2)

        # Ensure rank values are positive
        enhanced_df['rank'] = enhanced_df['rank'].apply(lambda x: max(0.1, x))

        return enhanced_df

    def filter_content(self, results_df):
        """
        Filter out low-quality or irrelevant content from search results.

        Args:
            results_df (DataFrame): DataFrame containing search results

        Returns:
            DataFrame: Filtered results
        """
        filtered_df = results_df.copy()

        # For each result, assess if it should be filtered out
        for idx, row in filtered_df.iterrows():
            # Skip if semantic score is already high
            if row.get('semantic_score', 0) >= 7.0:
                continue

            prompt = f"""
            Document Title: {row['title']}
            Document Snippet: {row['snippet']}

            Analyze if this content appears to be:
            1. Spam
            2. Content farm (low quality)
            3. Misleading
            4. Irrelevant to most searches

            Respond with either "FILTER" or "KEEP" without explanation.
            """

            try:
                response = self.model.generate_content(prompt)
                decision = response.text.strip().upper()

                if decision == "FILTER":
                    # Increase rank significantly (worse result)
                    filtered_df.at[idx, 'rank'] = filtered_df.at[idx, 'rank'] + 50
            except Exception as e:
                print(f"Error filtering result {idx}: {e}")

        return filtered_df

    def generate_improved_snippets(self, results_df):
        """
        Generate improved snippets for search results.

        Args:
            results_df (DataFrame): DataFrame containing search results

        Returns:
            DataFrame: Results with improved snippets
        """
        enhanced_df = results_df.copy()

        # Process only the top results to save API calls
        top_results = enhanced_df.sort_values('rank').head(5)

        for idx, row in top_results.iterrows():
            if len(row['html']) > 100:  # Only process if we have HTML content
                prompt = f"""
                Extract the most informative, concise summary from this HTML content.
                Create a snippet that is informative, factual, and directly addresses the likely user intent.
                Keep it under 200 characters.

                HTML Content: {row['html'][:10000]}  # Limit HTML to first 10K chars
                """

                try:
                    response = self.model.generate_content(prompt)
                    improved_snippet = response.text.strip()

                    # Update the snippet if we got a good response
                    if len(improved_snippet) > 20 and len(improved_snippet) < 250:
                        enhanced_df.at[idx, 'snippet'] = improved_snippet
                except Exception as e:
                    print(f"Error generating snippet for result {idx}: {e}")

        return enhanced_df