# Web Search Mining - Information Retrieval System

A Python-based Information Retrieval (IR) and Web Search Mining project designed for college-level learning. It illustrates the fundamental parts of a search engine, such as building an inverted index, handling Boolean AND queries, processing wildcards, and ranking results using TF-IDF and cosine similarity, all presented through a modern Tkinter graphical interface.

The current text corpus includes 19 plain-text documents featuring acts from well-known Shakespearean plays like *Hamlet*, *Macbeth*, *King Lear*, and *Henry IV*.

## 1. Project Objective

The goal is to demonstrate how a classic search engine processes a collection of text documents alongside a user's query to generate a ranked list of relevant results. This relies entirely on traditional IR methodologies (without the use of embeddings, machine learning models, or third-party search APIs).

## 2. Information Retrieval Pipeline

* Document Loading
* Tokenization
* Stop-word Removal
* Normalization
* Inverted Index Construction
* Query Processing
* Wildcard Processing
* Document Retrieval
* Ranking (TF-IDF & cosine similarity)
* GUI Display (featuring keyword-focused snippets)

Text diagram overview:

```text
               +-------------------+
   .txt files  |  document_loader  |  Returns doc_id -> filename, doc_id -> text
 ------------->|                   |
               +---------+---------+
                         |
                         v
               +-------------------+
               |  text_processor   |  Normalizes, tokenizes, removes stop words
               +---------+---------+
                         |
                         v
               +-------------------+
               |     indexer       |  Maps terms to {doc_ids} and term frequencies
               +---------+---------+
                         |
    query                v
   "king*"      +-------------------+
 ------------->| query_processor   |  Preprocesses query, handles wildcards,
               |   + wildcard      |  intersects posting lists (AND logic)
               +---------+---------+
                         |
                         v
               +-------------------+
               |      ranker       |  Calculates TF-IDF vectors & cosine similarity
               +---------+---------+
                         |
                         v
               +-------------------+
               |  search_engine    |  Outputs [{filename, score, preview}]
               +---------+---------+
                         |
                         v
               +-------------------+
               |       gui         |  Modern Tkinter: search bar, button, results display
               +-------------------+
```

## 3. Architecture

The Information Retrieval logic is strictly decoupled from the graphical user interface. The GUI simply invokes `SearchEngine.search()` and does not interact with the inverted index.

```text
project/
|
├── data_files/               19 text files of Shakespeare acts (*.txt)
|
├── src/
│   ├── document_loader.py    Reads .txt files, assigns unique integer doc IDs
│   ├── text_processor.py     Handles normalization, tokenization, stop-word removal
│   ├── indexer.py            Contains the InvertedIndex class
│   ├── query_processor.py    Contains QueryProcessor class (AND operations + wildcards)
│   ├── wildcard.py           Transforms wildcards to regex to find matching terms
│   ├── ranker.py             Contains Ranker class (TF-IDF and cosine similarity)
│   └── search_engine.py      Contains SearchEngine class (interface for the GUI)
|
├── gui.py                    Updated Tkinter user interface
├── main.py                   Initializes the index and opens the GUI
├── requirements.txt          (Only standard libraries used)
└── README.md
```

**Module Responsibilities:**
* `document_loader`: Reads all `.txt` files, skips unreadable ones, and returns mapping dictionaries for filenames and text content.
* `text_processor`: Provides a reusable `preprocess(text)` function for both documents and user queries.
* `indexer`: Constructs the `term -> set(doc_ids)` mapping, tracks term counts/lengths per document, and exposes the vocabulary.
* `wildcard`: Identifies `*` in terms and expands them to matching vocabulary words using regular expressions.
* `query_processor`: Cleans the query, processes wildcard terms, and fetches documents using AND logic.
* `ranker`: Calculates TF-IDF weights and sorts candidate documents based on cosine similarity against the query.
* `search_engine`: Connects all components and generates smart, keyword-centric text previews.
* `gui`: Provides a stylized input field, search button, and read-only results section.

## 4. Tokenization

The `text_processor.tokenize()` function divides the normalized text into individual word tokens based on whitespace. For this specific corpus, no further complexity is required.

## 5. Stop-word Removal

The `text_processor.remove_stop_words()` function eliminates common English words (and specific Shakespearean terms like *thou*, *thee*, *hath*, *doth*) using a predefined `STOP_WORDS` list. Removing these non-informative words reduces the index size, accelerating searches and enhancing ranking accuracy.

## 6. Normalization

The `text_processor.normalize()` function performs two primary tasks:
1. Converts all text to lowercase (ensuring `King` and `king` match).
2. Replaces non-alphanumeric characters (excluding `*`) with spaces, effectively removing punctuation while preserving wildcard symbols.

To maintain simplicity and clarity, no stemming or lemmatization techniques are applied.

## 7. Inverted Indexing

The `indexer.InvertedIndex` component is built once upon execution:

* `index`: Maps terms to sets of document IDs (posting lists), for example:
  ```python
  {
      "love":  {4, 5, 9, 12, ...},
      "death": {2, 4, 5, ...},
      "king":  {6, 7, 8, ...},
  }
  ```
* `term_freq`: A dictionary mapping document IDs to term occurrence frequencies (used for TF calculations).
* `doc_length`: Maps document IDs to their total token count.

Available methods include: `build()`, `lookup(term)`, `vocabulary()`, `document_count()`, and `term_frequency(term, doc_id)`.

## 8. Query Processing

The `query_processor.QueryProcessor.process(query)` routine:
1. Applies `preprocess()` to the query (using the same steps as document preprocessing).
2. Removes terms that are entirely empty or consist only of `*`.
3. Processes remaining terms:
   * If a `*` is present, it expands to all matching terms in the vocabulary and combines their posting lists (Union).
   * Otherwise, it directly retrieves the posting list for the term.
4. Performs an intersection (**AND** operation) across all query terms' posting lists.
5. Returns the resulting document IDs and the actual terms used, which are subsequently scored by the ranker.

*Example:* A query for `love death` will only retrieve documents containing both words.

## 9. Wildcard Processing

The `wildcard.expand(pattern, vocabulary)` function:
1. Retrieves the vocabulary list from the inverted index.
2. Translates the wildcard string into a regular expression, replacing `*` with `.*` and anchoring it.
3. Returns all terms from the vocabulary that fit the regex pattern.

Since `*` indicates "zero or more characters":
* `learn*` matches learn, learned, learning
* `*ing` matches king, thing, nothing, morning
* `mach*ne` matches machine

This operation scans through approximately 10k vocabulary terms linearly, which is virtually instantaneous.

## 10. TF-IDF Ranking

The `ranker.Ranker` implements the traditional vector space model:
* **Term Frequency (TF)**: `tf(t, d)` represents the raw count of term `t` in document `d`.
* **Inverse Document Frequency (IDF)**: `idf(t) = log(N / df(t))`, where `N` is total documents and `df(t)` is the number of documents with term `t`.
* **TF-IDF Weight**: `w(t, d) = tf(t, d) * idf(t)`.

Documents and queries are both modeled as vectors of TF-IDF weights.

## 11. Cosine Similarity

The relevance score of a document `d` given a query `q` is calculated as the cosine of the angle between their respective TF-IDF vectors.

```text
                 Sum over t of ( w(t, q) * w(t, d) )
cosine(q, d) = -------------------------------------------
                        ||q||  *  ||d||
```
This formula normalizes the score based on document length, preventing bias towards longer texts. The results are ordered by decreasing cosine similarity. To improve readability, a **relative score** percentage is also provided, comparing each result to the top match.

## 12. Smart Previews & GUI

The `search_engine.py` script creates dynamic, context-aware text snippets for the GUI, highlighting the specific terms matched in the document.

The `gui.py` interface features:
* A streamlined, professional search bar.
* A prominent Search button (also triggered by the Enter key).
* An elegantly formatted results display area.

Results display the ranking, filename, raw cosine score, relative score, and the matched text snippet. It also presents user-friendly alerts for errors like empty queries or no matching documents.

## 13. How to Run the Project

Requires Python 3.8+ with Tkinter support.
```bash
python main.py
```
This command initializes the index, prints basic statistics to the console, and launches the graphical interface.

## 14. Example Queries

* `love death`: Demonstrates multi-term AND logic.
* `king crown`: Searches across history and tragedy texts.
* `king*`: Prefix wildcard matching (e.g., kingdom, kings).
* `*ing`: Suffix wildcard matching (e.g., nothing, morning).
* `mach*ne`: Infix wildcard matching (e.g., machine).
* `the and of`: Stop words only (triggers a user message).
* `machine learning`: No results found (triggers a user message).

## 15. Limitations

* Exclusively supports AND queries (no OR, NOT, or phrase searching).
* Lacks stemming support (`love` vs `loving`).
* Uses raw term-frequency instead of advanced methods like BM25.
* Performs linear scanning for wildcard expansions.
* Index resides only in memory (rebuilt on startup).
* Does not understand semantic meaning or synonyms.

## 16. Possible Future Improvements

* Introduce a Boolean parser for OR/NOT logic and phrase queries.
* Implement a stemming algorithm (like Porter stemmer).
* Track term positions for proximity searches.
* Upgrade to BM25 or sublinear TF weighting.
* Serialize and save the index to disk for faster loading.
* Highlight exactly which terms matched within the GUI snippets.
