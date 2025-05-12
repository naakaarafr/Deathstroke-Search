
# 🌐 Gemini-Powered Smart Search Engine

A powerful and intelligent search engine that integrates Google Custom Search with Google's Gemini AI to enhance query understanding, semantic ranking, and content filtering. Built with Python and designed for improved relevancy and user-focused results.

---

## 🚀 Features

* 🔍 **Query Expansion** using Gemini AI for contextual improvements.
* 🧠 **Semantic Ranking** of results based on content relevance.
* 🚫 **Spam & Content Farm Filtering** for high-quality results.
* 🌐 **Country-Specific Search** with localized relevance.
* 🗃️ **SQLite Storage** to cache and reuse previous results.
* 🧾 **HTML Scraping** for content availability and analysis.
* 📦 Modular and extensible codebase.

---

## 🛠️ Tech Stack

* **Python 3.9+**
* **Google Custom Search API**
* **Google Gemini API (`gemini-2.0-flash`)**
* **Pandas & Requests**
* **SQLite (via `sqlite3`)**
* **dotenv for config management**

---

## 📁 Project Structure

```
.
├── app.py                   # Entry point (CLI/Flask ready)
├── search.py                # Main search logic and enhancements
├── gemini_integration.py    # Gemini-powered query enhancement and ranking
├── storage.py               # SQLite-based storage engine
├── filter.py                # (Optional) Custom filtering logic
├── blacklist.txt            # Blacklisted terms/domains (used in filter)
├── .env                     # Environment variables (API keys etc.)
```

---

## 🔐 .env File Format

```
SEARCH_KEY=your_google_search_api_key
SEARCH_ID=your_custom_search_engine_id
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🧪 Example Usage (from `search.py`)

```python
from search import search

query = "AI in Healthcare"
results_df = search(query, country="US")

print(results_df.head())
```

---

## ✅ Setup Instructions

1. **Clone the repo:**

   ```bash
   git clone https://github.com/your-username/smart-search-engine.git
   cd smart-search-engine
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the root directory and add your API keys.

4. **Run the script:**

   ```bash
   python app.py
   ```

---

## 📦 Optional Enhancements

* Add a Flask or FastAPI interface for a web-based UI.
* Integrate with vector databases for embedding-based search.
* Implement user feedback to update relevance scores in DB.

---

## 🧠 Credits

Built using:

* [Google Custom Search API](https://developers.google.com/custom-search)
* [Google Gemini (Generative AI)](https://ai.google.dev/)

---

## 📄 License

MIT License. See `LICENSE` file.


