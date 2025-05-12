import streamlit as st
from search import search
from filter import Filter
from storage import DBStorage
import pandas as pd
import time
import json
import requests

# Page configuration
st.set_page_config(
    page_title="Deathstroke-Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling with dark mode support
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 0rem 1rem;
    }

    /* Header styling - works in both light and dark mode */
    .search-header {
        background: linear-gradient(90deg, #7C4DFF 0%, #5E35B1 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }

    /* Search result styling - adapts to theme */
    .result-card {
        background-color: var(--background-color, rgba(255, 255, 255, 0.1));
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #7C4DFF;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }

    /* Gemini badge styling */
    .gemini-badge {
        background-color: #34A853;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
    }

    /* Country badge styling */
    .country-badge {
        background-color: #4285F4;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
    }

    /* Light mode specific styles */
    [data-theme="light"] .result-card, .light-mode .result-card {
        background-color: white;
    }

    /* Dark mode specific styles */
    [data-theme="dark"] .result-card, .dark-mode .result-card {
        background-color: rgba(255, 255, 255, 0.05);
    }

    .site-url {
        font-size: 0.8rem;
        color: #4CAF50;
        margin-bottom: 0.3rem;
    }

    .result-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #BB86FC;
        margin-bottom: 0.5rem;
        text-decoration: none;
    }

    .result-title:hover {
        text-decoration: underline;
    }

    .snippet {
        font-size: 0.9rem;
        line-height: 1.4;
        margin-bottom: 0.5rem;
        /* Color will adapt to theme */
    }

    .rank-badge {
        background-color: rgba(124, 77, 255, 0.15);
        color: #BB86FC;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    .relevant-button {
        background-color: rgba(76, 175, 80, 0.1);
        color: #69F0AE;
        border: 1px solid #69F0AE;
        border-radius: 4px;
        padding: 0.3rem 0.6rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }

    .relevant-button:hover {
        background-color: #69F0AE;
        color: #121212;
    }

    /* Search form styling - adapts to theme */
    .search-container {
        background-color: var(--background-color, rgba(255, 255, 255, 0.05));
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 2rem;
    }

    /* Light mode specific styles */
    [data-theme="light"] .search-container, .light-mode .search-container {
        background-color: white;
    }

    /* Dark mode specific styles */
    [data-theme="dark"] .search-container, .dark-mode .search-container {
        background-color: rgba(255, 255, 255, 0.05);
    }

    /* Loading spinner */
    .stSpinner > div {
        border-color: #BB86FC !important;
    }

    /* Pagination styling */
    .pagination-container {
        display: flex;
        justify-content: center;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    .page-button {
        background-color: rgba(124, 77, 255, 0.15);
        color: #BB86FC;
        border: 1px solid #7C4DFF;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        margin: 0 0.25rem;
        cursor: pointer;
        transition: all 0.3s;
    }

    .page-button:hover {
        background-color: rgba(124, 77, 255, 0.3);
    }

    .page-button.active {
        background-color: #7C4DFF;
        color: white;
    }

    .page-info {
        padding: 0.5rem 1rem;
        color: var(--text-color);
    }

    /* Detect theme by first checking Streamlit theme, then falling back to prefers-color-scheme */
    :root {
        color-scheme: light dark;
    }

    /* Dynamic theme detection script */
    .stApp {
        --background-color: white;
    }

    /* Apply dark theme if auto dark mode is enabled */
    @media (prefers-color-scheme: dark) {
        .stApp {
            --background-color: rgba(255, 255, 255, 0.05);
        }
    }
</style>
""", unsafe_allow_html=True)


def get_user_country():
    """Attempt to get user's country from IP address using ipinfo.io"""
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        return data.get('country', None)  # Returns two-letter country code like 'US'
    except:
        return None


# Country name mapping (for display purposes)
def get_country_list():
    return {
        "US": "United States",
        "GB": "United Kingdom",
        "CA": "Canada",
        "AU": "Australia",
        "DE": "Germany",
        "FR": "France",
        "JP": "Japan",
        "IN": "India",
        "BR": "Brazil",
        "MX": "Mexico",
        "ES": "Spain",
        "IT": "Italy",
        "NL": "Netherlands",
        "RU": "Russia",
        "CN": "China",
        "KR": "South Korea",
        "ZA": "South Africa",
        "SG": "Singapore",
        "SE": "Sweden",
        "CH": "Switzerland",
        # Add more countries as needed
    }


def show_search_header():
    st.markdown("""
    <div class="search-header">
        <h1>🔍 Deathstroke - Search</h1>
        <p>AI-enhanced search with query expansion, semantic ranking, and location-aware results</p>
    </div>
    """, unsafe_allow_html=True)


def show_search_form():
    with st.container():
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        with st.form(key="search_form"):
            # First row: search query
            query = st.text_input("",
                                  value=st.session_state.get("query", ""),
                                  placeholder="Enter your search query here...",
                                  label_visibility="collapsed")

            # Second row: country selector and search button
            col1, col2 = st.columns([3, 1])

            with col1:
                # Country selector
                countries = get_country_list()
                country_options = ["Global (No location filter)"] + [f"{code} - {name}" for code, name in
                                                                     countries.items()]

                # Try to get user's country for default selection
                default_country = get_user_country()
                default_index = 0

                if default_country and default_country in countries:
                    try:
                        default_index = country_options.index(f"{default_country} - {countries[default_country]}")
                    except ValueError:
                        default_index = 0

                selected_country = st.selectbox(
                    "Country/Region for results:",
                    options=country_options,
                    index=default_index
                )

            with col2:
                submitted = st.form_submit_button("🔍 Search")

            if submitted and query:
                st.session_state.query = query

                # Reset pagination when new search is performed
                st.session_state.page = 1

                # Clear previous search results when a new search is performed
                if 'all_results_df' in st.session_state:
                    del st.session_state.all_results_df

                # Parse country code from selection
                if selected_country != "Global (No location filter)":
                    country_code = selected_country.split(" - ")[0]
                    st.session_state.country = country_code
                else:
                    st.session_state.country = None

                st.session_state.search_performed = True
                return query, st.session_state.country

        st.markdown('</div>', unsafe_allow_html=True)
    return None, None


def display_result(index, row):
    # Check if this result has been semantically ranked (if that field exists)
    has_semantic_ranking = 'semantic_score' in row
    # Check if country filter was applied
    has_country_filter = 'country' in st.session_state and st.session_state.country is not None

    with st.container():
        gemini_badge = f'<span class="gemini-badge">Gemini Enhanced</span>' if has_semantic_ranking else ""
        country_badge = f'<span class="country-badge">{st.session_state.country}</span>' if has_country_filter else ""

        st.markdown(f"""
        <div class="result-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex-grow: 1;">
                    <p class="site-url">{row['link']}</p>
                    <a href="{row['link']}" target="_blank" class="result-title">{row['title']}</a> {gemini_badge} {country_badge}
                    <p class="snippet">{row['snippet']}</p>
                    <span class="rank-badge">Rank: {float(row['rank']):.1f}</span>
                </div>
                <div>
                    <div id="btn_placeholder_{index}"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # We still need the actual button for functionality
        if st.button("Mark Relevant", key=f"rel_{index}", help="Mark this result as relevant for your search"):
            mark_relevant(st.session_state.query, row['link'])


def mark_relevant(query, link):
    storage = DBStorage()
    storage.update_relevance(query, link, 10)
    st.success(f"✅ Marked as relevant")
    time.sleep(1)
    st.rerun()


def show_sidebar_info():
    with st.sidebar:
        st.title("Search Options")

        st.subheader("About this search engine")
        st.info("""
        This advanced search application uses Google's Gemini AI to enhance search results:
        - Query expansion improves search accuracy
        - Semantic ranking provides more relevant results
        - Content filtering removes low-quality sites
        - Country-specific searches for local results
        - AI-generated snippets summarize content better
        """)

        # Theme toggle
        st.subheader("Appearance")
        if 'theme' not in st.session_state:
            st.session_state.theme = "auto"

        theme = st.radio(
            "Choose theme",
            options=["Auto", "Light", "Dark"],
            horizontal=True,
            index=0,
            help="Select your preferred theme"
        )

        if theme == "Light":
            st.session_state.theme = "light"
            st.markdown("""
            <style>
                .stApp {
                    --background-color: white !important;
                }
                body {
                    color-scheme: light;
                }
            </style>
            """, unsafe_allow_html=True)
        elif theme == "Dark":
            st.session_state.theme = "dark"
            st.markdown("""
            <style>
                .stApp {
                    --background-color: rgba(255, 255, 255, 0.05) !important;
                }
                body {
                    color-scheme: dark;
                }
            </style>
            """, unsafe_allow_html=True)

        # Add some example searches
        st.subheader("Try these searches")
        example_searches = [
            "Python programming",
            "Machine learning tutorials",
            "Data visualization best practices",
            "Web development frameworks 2025",
            "Local restaurants"  # This one benefits from country context
        ]

        for example in example_searches:
            if st.button(example):
                st.session_state.query = example
                st.session_state.search_performed = True
                # Reset pagination when a new example search is clicked
                st.session_state.page = 1

                # Clear previous search results when using an example
                if 'all_results_df' in st.session_state:
                    del st.session_state.all_results_df

                st.rerun()


def run_search(query, country=None):
    with st.spinner("Searching with AI-enhanced results..."):
        # The search function now integrates Gemini for better results
        results = search(query, country=country)

        # We still apply our traditional filtering as well
        fi = Filter(results)
        filtered = fi.filter()

        return filtered


def display_pagination(total_results, results_per_page):
    """
    Display pagination controls for search results

    Args:
        total_results (int): Total number of search results
        results_per_page (int): Number of results per page
    """
    # Calculate total pages needed
    total_pages = max(1, (total_results + results_per_page - 1) // results_per_page)

    # Get current page from session state
    current_page = st.session_state.page

    # Determine if previous/next buttons should be enabled
    prev_disabled = current_page <= 1
    next_disabled = current_page >= total_pages

    # Create pagination UI
    st.markdown('<div class="pagination-container">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])

    with col1:
        if st.button("◀ Previous", disabled=prev_disabled):
            st.session_state.page = max(1, current_page - 1)
            st.rerun()

    with col2:
        if st.button("Next ▶", disabled=next_disabled):
            st.session_state.page = min(total_pages, current_page + 1)
            st.rerun()

    with col3:
        page_info = f"Page {current_page} of {total_pages} | " \
                    f"Showing results {(current_page - 1) * results_per_page + 1}-" \
                    f"{min(current_page * results_per_page, total_results)} of {total_results}"
        st.markdown(f"<div class='page-info'>{page_info}</div>", unsafe_allow_html=True)

    with col4:
        # Add a direct page selection dropdown for quick navigation
        if total_pages > 1:
            page_options = [f"Page {i}" for i in range(1, total_pages + 1)]
            selected_page = st.selectbox(
                "",
                options=page_options,
                index=current_page - 1,
                label_visibility="collapsed"
            )
            if f"Page {current_page}" != selected_page:
                st.session_state.page = int(selected_page.split(" ")[1])
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# Initialize session state
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'country' not in st.session_state:
    # Try to get user's country for first visit
    st.session_state.country = get_user_country()
if 'page' not in st.session_state:
    st.session_state.page = 1

# Main app layout
show_search_header()
query_result, country = show_search_form()
show_sidebar_info()

# Display search results
if st.session_state.search_performed:
    # Get all results only if we don't already have them stored
    if 'all_results_df' not in st.session_state:
        all_results_df = run_search(st.session_state.query, country=st.session_state.country)
        # Store the entire results dataframe in session state
        st.session_state.all_results_df = all_results_df
    else:
        # Use the stored results
        all_results_df = st.session_state.all_results_df

    # Define results per page
    results_per_page = 10
    total_results = len(all_results_df)

    # Results summary
    location_info = f" in {st.session_state.country}" if st.session_state.country else ""
    st.markdown(f"### Found {total_results} results for \"{st.session_state.query}\"{location_info}")

    # Calculate pagination
    start_idx = (st.session_state.page - 1) * results_per_page
    end_idx = min(start_idx + results_per_page, total_results)

    # Get the current page results
    current_page_results = all_results_df.iloc[start_idx:end_idx]

    # Display results for current page
    for index, row in current_page_results.iterrows():
        display_result(index, row)

    # Display pagination controls
    if total_results > results_per_page:
        display_pagination(total_results, results_per_page)