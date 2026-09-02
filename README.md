# Web Search Mining - Information Retrieval System

A Python-based **Information Retrieval (IR) and Web Search Mining system** built for learning and demonstrating the core components of a traditional search engine.

The system indexes a local Shakespeare corpus and supports **Boolean retrieval, phrase searching, wildcard queries, TF-IDF ranking, cosine similarity, spelling suggestions, context-aware previews, and result pagination** through a Tkinter desktop interface.

The bundled corpus contains **19 plain-text acts** from *Hamlet*, *Macbeth*, *King Lear*, and *Henry IV*.

---

## 1. Project Features

- Positional inverted index built entirely in the memory.
- Text normalization and tokenization.
- Stop-word removal.
- Boolean search with:
  - `AND`
  - `OR`
  - `NOT`
  - Parentheses
- Implicit `AND` between adjacent terms.
- Quoted phrase searching.
- Wildcard searching using `*`.
- Prefix, suffix, and infix wildcard support.
- Wildcards inside quoted phrases.
- TF-IDF document ranking.
- Cosine similarity scoring.
- Relative relevance percentage.
- Context-aware keyword-focused previews.
- Highlighted query matches in results.
- Result pagination with **5 results per page**.
- Helpful handling of:
  - Blank queries
  - Malformed Boolean expressions
  - Stop-word-only queries
  - Queries with no matching documents
- **"Did you mean?"** spelling suggestions for unsuccessful searches.
- No third-party Python dependencies.

---

## 2. Project Objective

The objective of this project is to demonstrate how a traditional information retrieval system processes documents and user queries to retrieve and rank relevant documents.

The system follows a classical search-engine pipeline:

```text
Documents
    ↓
Document Loading
    ↓
Text Preprocessing
    ↓
Positional Inverted Index
    ↓
User Query
    ↓
Query Parsing
    ↓
Wildcard / Phrase Processing
    ↓
Boolean Retrieval
    ↓
TF-IDF Ranking
    ↓
Cosine Similarity
    ↓
Search Results
    ↓
Previews + Highlighting + Pagination
```

The project focuses on **traditional information retrieval techniques** rather than embeddings, large language models, machine learning models, or external search APIs.

---

# 3. System Architecture

The IR logic is separated from the graphical interface. The GUI communicates with the system through the `SearchEngine.search()` interface rather than directly interacting with the inverted index.

```text
                         +----------------------+
                         |      .txt Corpus     |
                         |  19 Shakespeare Acts |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |  document_loader.py  |
                         |  Load documents      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |  text_processor.py   |
                         | Normalize             |
                         | Tokenize              |
                         | Remove stop words     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      indexer.py      |
                         | Positional Inverted   |
                         | Index + Statistics    |
                         +----------+-----------+
                                    |
                                    |
                       User Query   |
                           |        |
                           v        |
                  +-------------------------+
                  |   query_processor.py    |
                  |                         |
                  | Boolean Parsing         |
                  | Phrase Matching         |
                  | Wildcard Expansion      |
                  +-----------+-------------+
                              |
                              v
                  +-------------------------+
                  |       Candidate Docs    |
                  +-----------+-------------+
                              |
                              v
                  +-------------------------+
                  |        ranker.py        |
                  |                         |
                  | TF-IDF                  |
                  | Cosine Similarity       |
                  +-----------+-------------+
                              |
                              v
                  +-------------------------+
                  |    search_engine.py     |
                  |                         |
                  | Ranking + Previews      |
                  | Highlighting            |
                  | Suggestions             |
                  +-----------+-------------+
                              |
                              v
                  +-------------------------+
                  |        gui.py            |
                  |                         |
                  | Search + Results        |
                  | Pagination              |
                  +-------------------------+
```

---

# 4. Project Structure

```text
WSM_Project/
│
├── data_files/
│   └── 19 Shakespeare text files
│
├── src/
│   ├── document_loader.py
│   ├── text_processor.py
│   ├── indexer.py
│   ├── wildcard.py
│   ├── query_processor.py
│   ├── ranker.py
│   └── search_engine.py
│
├── gui.py
├── main.py
├── requirements.txt
└── README.md
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `document_loader.py` | Loads valid `.txt` documents and assigns document IDs |
| `text_processor.py` | Normalizes text, tokenizes content, and removes stop words |
| `indexer.py` | Builds and stores the positional inverted index |
| `wildcard.py` | Expands wildcard patterns against the vocabulary |
| `query_processor.py` | Parses Boolean expressions and evaluates terms, phrases, and wildcards |
| `ranker.py` | Calculates TF-IDF weights and cosine similarity |
| `search_engine.py` | Provides the main search API, previews, highlighting, and spelling suggestions |
| `gui.py` | Provides the Tkinter search interface and paginated results |
| `main.py` | Initializes the application and starts the GUI |

---

# 5. Document Loading

The `document_loader.py` module loads all valid `.txt` files from the corpus.

Each document receives a unique integer document ID.

The loader maintains information such as:

```text
doc_id → filename
doc_id → document text
```

Unreadable or invalid files are skipped rather than terminating the entire application.

---

# 6. Text Preprocessing

The `text_processor.py` module provides preprocessing functions shared by both documents and user queries.

The preprocessing pipeline consists of:

```text
Raw Text
   ↓
Normalization
   ↓
Tokenization
   ↓
Stop-word Removal
   ↓
Processed Tokens
```

## Normalization

Text is converted to lowercase so that terms such as:

```text
King
KING
king
```

are treated as the same term.

Punctuation and non-alphanumeric characters are removed while preserving wildcard characters when required for query processing.

---

## Tokenization

The tokenizer converts text into individual terms.

For example:

```text
The king entered the castle.
```

may become:

```text
the
king
entered
the
castle
```

before stop-word removal.

---

## Stop-word Removal

Common English words are removed using a predefined `STOP_WORDS` list.

The list also includes frequently occurring Shakespearean terms such as:

```text
thou
thee
hath
doth
```

Removing such terms reduces unnecessary index entries and allows more meaningful terms to influence retrieval and ranking.

---

# 7. Positional Inverted Index

The `indexer.py` module builds a **positional inverted index**.

Unlike a simple inverted index that stores only document IDs, the positional index also stores the positions where each term occurs.

For example:

```python
{
    "king": {
        1: [14, 57],
        4: [8]
    }
}
```

This means:

- `king` occurs in document `1` at positions `14` and `57`.
- `king` occurs in document `4` at position `8`.

The positional information is essential for **phrase searching**.

The index also maintains:

- Document term frequencies
- Document lengths
- Document count
- Vocabulary

Important operations include:

```text
build()
lookup(term)
vocabulary()
document_count()
term_frequency(term, doc_id)
```

---

# 8. Query Processing

The `query_processor.py` module parses and evaluates user queries.

The system supports:

- Individual terms
- `AND`
- `OR`
- `NOT`
- Parentheses
- Implicit `AND`
- Quoted phrases
- Wildcard terms
- Wildcard phrases

## Boolean Operator Precedence

Boolean operators are evaluated in the following order:

```text
1. NOT
2. AND
3. OR
```

Parentheses can be used to override the default precedence.

For example:

```text
king OR queen AND crown
```

is evaluated as:

```text
king OR (queen AND crown)
```

while:

```text
(king OR queen) AND crown
```

forces the grouped expression to be evaluated first.

---

# 9. Implicit AND

Adjacent terms are automatically interpreted as an `AND` expression.

For example:

```text
king crown
```

is treated as:

```text
king AND crown
```

Therefore, a document must contain both terms to become a candidate result.

---

# 10. Phrase Searching

Quoted queries are interpreted as phrases.

For example:

```text
"my lord"
```

requires the processed terms to occur consecutively in the document.

The positional inverted index makes this possible by comparing the positions of consecutive terms.

Phrase searching can also be combined with other query features.

For example:

```text
"my king*"
```

uses a wildcard inside a phrase.

---

# 11. Wildcard Processing

The `wildcard.py` module handles wildcard expansion.

The `*` character represents **zero or more characters**.

Wildcard patterns can appear at different positions within a term.

## Prefix Wildcard

```text
king*
```

Can match terms such as:

```text
king
kings
kingdom
```

## Suffix Wildcard

```text
*ing
```

Can match terms such as:

```text
king
thing
nothing
morning
```

## Infix Wildcard

```text
mach*ne
```

Can match terms such as:

```text
machine
```

## Wildcard Inside a Phrase

```text
"my king*"
```

The wildcard is expanded against the vocabulary and the resulting terms are evaluated using phrase-position matching.

Wildcard expansion currently scans the vocabulary linearly.

---

# 12. Boolean Retrieval

The query processor evaluates Boolean expressions by operating on posting lists.

### AND

```text
king AND crown
```

Returns documents containing both terms.

Conceptually:

```text
posting(king) ∩ posting(crown)
```

### OR

```text
king OR queen
```

Returns documents containing either term.

Conceptually:

```text
posting(king) ∪ posting(queen)
```

### NOT

```text
king AND NOT crown
```

Returns documents containing `king` while excluding documents containing `crown`.

### Parentheses

```text
(king OR queen) AND crown
```

allows more complex expressions to be represented explicitly.

---

# 13. TF-IDF Ranking

After Boolean retrieval determines the candidate documents, the `ranker.py` module ranks them using **TF-IDF**.

The system uses:

### Term Frequency

```text
tf(t,d)
```

represents the number of occurrences of term `t` in document `d`.

### Inverse Document Frequency

```text
idf(t) = log(N / df(t))
```

where:

- `N` = total number of documents
- `df(t)` = number of documents containing term `t`

### TF-IDF Weight

```text
w(t,d) = tf(t,d) × idf(t)
```

Both queries and documents are represented using TF-IDF vectors.

---

# 14. Cosine Similarity

Candidate documents are ranked using cosine similarity between the query vector and document vector.

```text
                  Σ w(t,q) × w(t,d)
cosine(q,d) = -----------------------------
                 ||q|| × ||d||
```

A higher cosine similarity indicates that the document is more relevant to the query according to the TF-IDF vector-space model.

Results are sorted in descending order of cosine similarity.

The interface displays:

- Raw cosine score
- Relative relevance percentage
- Result ranking

The relative relevance percentage compares a result's score with the highest-ranked result.

---

# 15. Search Engine

The `search_engine.py` module acts as the main interface between the retrieval system and the GUI.

It coordinates:

```text
Query
 ↓
Query Processing
 ↓
Boolean / Phrase Matching
 ↓
Candidate Documents
 ↓
TF-IDF Ranking
 ↓
Preview Generation
 ↓
Match Highlighting
 ↓
Search Response
```

The search engine also provides spelling suggestions when no matching documents are found.

---

# 16. Context-Aware Previews

Instead of displaying an entire document, the search engine generates a keyword-focused preview around relevant matches.

For example, a result may display a small section of the document surrounding the matched query term.

This makes the results easier to scan and more similar to the behaviour of a real search engine.

Matched terms are also highlighted in the result preview.

---

# 17. Pagination

Search results are displayed using pagination to prevent large result sets from overwhelming the interface.

The GUI displays:

```text
5 results per page
```

Users can navigate between result pages.

This keeps the interface compact while still allowing the complete result set to be explored.

---

# 18. Search Response Statuses

`SearchEngine.search(query)` returns structured search results with different statuses.

### `ok`

Matching documents were found successfully.

### `empty`

The user submitted a blank query.

### `only_stopwords`

The query contained only stop words, leaving no searchable terms.

### `no_match`

The query was valid but no documents matched.

A spelling suggestion may be provided in this case.

### `query_error`

The Boolean expression was malformed.

For example:

```text
hamlet AND
```

produces an invalid-query response.

---

# 19. Spelling Suggestions

When a valid query produces no results, the system can provide a **"Did you mean?"** suggestion.

For example:

```text
hamelt
```

may result in a suggestion such as:

```text
Did you mean: hamlet?
```

This improves usability when users make small spelling mistakes.

---

# 20. Graphical User Interface

The application uses **Tkinter** for its desktop interface.

The GUI provides:

- Search input field
- Search button
- Enter-key search
- Ranked results
- Filename display
- Cosine similarity score
- Relative relevance
- Context-aware previews
- Highlighted matches
- Pagination controls
- User-friendly error messages
- Spelling suggestions

The GUI does not directly manipulate the index. It communicates with the search system through the search engine interface.

---

# 21. Example Queries

| Query | Behaviour |
|---|---|
| `hamlet` | Finds documents containing `hamlet` |
| `king lear` | Implicit `AND`; both terms must appear |
| `king AND crown` | Explicit `AND` search |
| `king OR queen` | Finds documents containing either term |
| `king AND NOT crown` | Finds `king` while excluding `crown` |
| `(king OR queen) AND crown` | Boolean expression using parentheses |
| `"my lord"` | Exact processed phrase search |
| `king*` | Prefix wildcard search |
| `*ing` | Suffix wildcard search |
| `mach*ne` | Infix wildcard search |
| `"my king*"` | Phrase search containing a wildcard |
| `hamelt` | May provide a spelling suggestion |
| `hamlet AND` | Invalid Boolean query |

---

# 22. Search Pipeline Example

Consider the query:

```text
(king OR queen) AND crown
```

The system processes it approximately as follows:

```text
User Query
    ↓
Tokenization / Normalization
    ↓
Boolean Parsing
    ↓
Evaluate:
    (king OR queen)
    ↓
Union of posting lists
    ↓
AND with crown
    ↓
Candidate Documents
    ↓
TF-IDF Calculation
    ↓
Cosine Similarity
    ↓
Sort by Score
    ↓
Generate Context Preview
    ↓
Highlight Matches
    ↓
Display Paginated Results
```

---

# 23. How to Run

## Requirements

- Python **3.8 or newer**
- Tkinter support
- No third-party Python packages required

Run the application from the project directory:

```bash
python main.py
```

The application will:

1. Load the Shakespeare corpus.
2. Preprocess the documents.
3. Build the positional inverted index.
4. Print document and vocabulary statistics in the terminal.
5. Launch the Tkinter search interface.

---
