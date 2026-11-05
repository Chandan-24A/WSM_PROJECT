# Information Retrieval System (WSM Project)

A graduation-level **Information Retrieval (IR) and Web Search & Mining (WSM) System** indexing a local Shakespeare corpus (19 acts from *Hamlet, Macbeth, King Lear, Henry IV*).

---

## Student & Project Metadata

| Field | Details |
|---|---|
| **Student Name** | Chandan Kumar Sahoo |
| **Student ID** | B524024 |
| **Branch** | Computer Engineering |
| **Course** | Web Search & Mining (WSM) |
| **Assignment** | Graduation-Level WSM Assignment & Implementation |
| **Report Document** | `Information_Retrieval_System_Project_Report.pdf` |

---

## 1. Syllabus & Curriculum Features Implemented

### 1. Inverted Index Construction
- **Positional Inverted Index**: Maps each term to document IDs and token positions (`term -> doc_id -> [positions]`).
- Preserves exact document token positions so that phrase queries with stop words (e.g. `"to be or not to be"`, `"my lord"`) match consecutive occurrences.
- Computes term frequencies, document lengths, and corpus vocabulary.

### 2. Tolerant Retrieval & Wildcard Matching
- **$k$-gram Index**: 3-gram character index on vocabulary terms (`$term$`) for fast candidate selection.
- Supports prefix (`king*`), suffix (`*ing`), and infix (`mach*ne`) wildcards.
- **"Did you mean?" Spelling Correction**: Dynamic programming Levenshtein edit distance for query typo tolerance.

### 3. Boolean & Exact Phrase Retrieval
- Evaluates Boolean operators (`AND`, `OR`, `NOT`, parentheses) using Shunting-Yard infix-to-postfix conversion.
- Operator precedence: `NOT` > `AND` > `OR`.
- Supports implicit `AND` between adjacent terms and exact multi-word quoted phrase matching.

### 4. Vector Space Model (VSM) Retrieval
- Document and query representation in a shared vector space.
- **TF-IDF Weighting**:
  - Sublinear Term Frequency: $w_{\text{tf}} = 1 + \ln(\text{tf})$.
  - Smoothed Inverse Document Frequency: $\text{IDF} = \ln(1 + N / \text{df})$, preventing ubiquitous terms (e.g., `king`, `lord`) from collapsing to zero.
- **Cosine Similarity**: Cosine of the angle between query vector and document vector with $L_2$ Euclidean normalization:
  $$\text{Cosine}(q, d) = \frac{\sum_{t \in q \cap d} w_{t,q} \cdot w_{t,d}}{\|q\|_2 \cdot \|d\|_2}$$

### 5. Link Analysis & PageRank
- Constructs a directed document graph from narrative act transitions ($Act_i \to Act_{i+1}$) and cross-act dramatic references.
- Implements the standard **Power Iteration PageRank Algorithm** ($d = 0.85, \epsilon = 10^{-6}$):
  $$P(u) = \frac{1 - d}{N} + d \sum_{v \in M(u)} \frac{P(v)}{L(v)}$$
- Allows hybrid score blending: $\text{Score} = (1 - \alpha) \cdot \text{VSM} + \alpha \cdot \text{PageRank}$.

### 6. Query Expansion
- **Thesaurus Expansion**: Semantic synonym associations for early modern dramatic vocabulary.
- **Rocchio Pseudo-Relevance Feedback (PRF)**: Extracts high-IDF informative terms from top-ranked candidate documents to enrich the query vector.

### 7. Opinion Mining & Sentiment Analysis
- Valence-based dramatic lexicon scoring positive, negative, and neutral emotion.
- Accounts for intensifiers and 2-word negation windows (*"not guilty", "nor villain"*).
- **Character Opinion Miner**: Mines dialogue and sentiment surrounding specific figures (*Hamlet, Falstaff, Lady Macbeth, Duncan, Lear*).

### 8. Standard IR Evaluation Framework
- Benchmark suite evaluated against ground-truth relevance sets across standard queries.
- Computes:
  - **Precision@5 ($P@5$)** and **Recall@5 ($R@5$)**
  - **F1-Score ($F_1@5$)**
  - **Average Precision (AP)** and **Mean Average Precision (MAP)**
  - **Reciprocal Rank (RR)** and **Mean Reciprocal Rank (MRR)**
  - **Normalized Discounted Cumulative Gain (NDCG@5)**

---

## 2. Modern Web Application Interface

Converted from the desktop GUI to a modern, responsive web application:
- **Search Engine Tab**: Instant search, autocomplete suggestions, quick query chips, relevance progress bars, PageRank badges, sentiment tags, and snippet term highlighting.
- **PageRank Graph Tab**: In-degree, out-degree, and authority scores table for all 19 acts.
- **Opinion Mining Tab**: Play emotional trajectories and interactive character opinion extractor.
- **Evaluation Suite Tab**: One-click benchmark runner with live MAP, MRR, Precision, and NDCG scorecards.
- **Corpus Library Tab**: Collection browser with native `<dialog>` full text reader.

---

## 3. How to Run

1. Navigate to the project directory:
   ```powershell
   cd D:\WSM_ASSIGNMENT\WSM_Project
   ```
2. Start the web application:
   ```powershell
   python main.py
   ```
3. Open your browser:
   ```text
   http://127.0.0.1:5000
   ```

*(To run the desktop Tkinter interface instead, run `python main.py --gui`.)*

---

## 4. Academic Project Report (PDF)

A 6-page project report is included:
- **File**: `Information_Retrieval_System_Project_Report.pdf` (and `Information_Retrieval_System_Report.pdf`)
- **Metadata**:
  - **Student Name**: Chandan Kumar Sahoo
  - **ID**: B524024
  - **Branch**: Computer Engineering
  - **Course**: Web Search & Mining (WSM)
- **Contents**:
  - Full system architecture and module pipeline breakdown
  - Inverted index & phrase verification mathematical algorithms
  - Tolerant retrieval with 3-gram index and dynamic programming Levenshtein distance
  - Vector Space Model (TF-IDF Cosine similarity) formulation and Rocchio PRF
  - Power-Iteration PageRank algorithm, transition matrices, and hybrid ranking
  - Domain valence sentiment lexicon and character opinion mining
  - Empirical evaluation benchmark suite (MAP, MRR, P@5, NDCG@5)
  - Full project summary matrix and annotated UI figure captures

---

## 5. Project Directory Structure

```text
WSM_Project/
├── app.py                                       # Flask REST API server and routes
├── gui.py                                       # Standalone Tkinter desktop interface
├── main.py                                      # Unified CLI / web entrypoint
├── requirements.txt                             # Python dependencies
├── README.md                                    # Project documentation
├── Information_Retrieval_System_Project_Report.pdf  # 6-page Academic PDF Report
├── data_files/                                  # 19 Shakespeare Acts (Hamlet, Macbeth, Lear, Henry IV)
├── report_assets/                               # UI figures and visualization assets
├── src/
│   ├── document_loader.py                       # Corpus loading and metadata extraction
│   ├── text_processor.py                        # Linguistic normalizer, stemmer, stopword filter
│   ├── indexer.py                               # Positional inverted index & 3-gram builder
│   ├── wildcard.py                              # Tolerant retrieval & Levenshtein spellchecker
│   ├── query_processor.py                       # Shunting-Yard Boolean parser & phrase verifier
│   ├── ranker.py                                # Vector Space Model (TF-IDF Cosine ranker)
│   ├── pagerank.py                              # Power Iteration PageRank graph analyzer
│   ├── query_expansion.py                       # Thesaurus & Rocchio PRF query expander
│   ├── sentiment.py                             # Valence lexicon & character opinion miner
│   └── evaluation.py                            # IR benchmark metrics (MAP, MRR, NDCG)
├── static/
│   ├── app.js                                   # Interactive single-page application frontend
│   └── style.css                                # Modern responsive styles & animations
└── templates/
    └── index.html                               # Modern HTML5 web application template
```
