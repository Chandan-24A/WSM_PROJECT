import re
from src.document_loader import load_documents
from src.indexer import InvertedIndex
from src.query_processor import QueryProcessor
from src.ranker import Ranker
from src.wildcard import KGramIndex
from src.pagerank import PageRank
from src.query_expansion import QueryExpander
from src.sentiment import SentimentAnalyzer
from src.evaluation import IREvaluator
from src.text_processor import preprocess


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


class SearchEngine:
    """Core Information Retrieval & Web Search Mining Engine."""

    def __init__(self, documents_dir):
        self.documents_dir = documents_dir
        self.doc_filenames = {}
        self.doc_texts = {}
        self.index = None
        self.kgram_index = None
        self.query_processor = None
        self.ranker = None
        self.pagerank = None
        self.query_expander = None
        self.sentiment_analyzer = None
        self.evaluator = None

    def build_index(self):
        self.doc_filenames, self.doc_texts = load_documents(self.documents_dir)
        self.index = InvertedIndex()
        self.index.build(self.doc_texts)

        # Build 3-gram index for fast tolerant retrieval and wildcard expansion
        self.kgram_index = KGramIndex(k=3)
        self.kgram_index.build(self.index.vocabulary(include_stopwords=True))

        self.query_processor = QueryProcessor(self.index, self.kgram_index)
        self.ranker = Ranker(self.index)
        self.pagerank = PageRank(self.doc_filenames, self.doc_texts)
        self.query_expander = QueryExpander(self.index, self.ranker)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.evaluator = IREvaluator(self)

    def preview(self, doc_id, matched_terms=None, length=260):
        text = re.sub(r"\s+", " ", self.doc_texts.get(doc_id, "")).strip()

        if matched_terms:
            text_lower = text.lower()
            match_idx = -1
            for term in matched_terms:
                idx = text_lower.find(term.lower())
                if idx != -1 and (match_idx == -1 or idx < match_idx):
                    match_idx = idx

            if match_idx != -1:
                start = max(0, match_idx - length // 2)
                end = min(len(text), match_idx + length // 2)
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                return snippet

        if len(text) > length:
            return text[:length] + "..."
        return text

    def did_you_mean(self, query):
        tokens = re.findall(r'\(|\)|AND|OR|NOT|[\w\*]+', query)
        vocab = self.index.vocabulary(include_stopwords=False)
        corrected = []
        changed = False

        for token in tokens:
            if token in ('AND', 'OR', 'NOT', '(', ')') or '*' in token:
                corrected.append(token)
            else:
                prep = preprocess(token, keep_stopwords=False)
                if not prep:
                    corrected.append(token)
                    continue
                t = prep[0]
                if t in self.index.index:
                    corrected.append(token)
                else:
                    best_match = t
                    min_dist = 999
                    for v in vocab:
                        if abs(len(v) - len(t)) > 2:
                            continue
                        d = levenshtein(t, v)
                        if d < min_dist:
                            min_dist = d
                            best_match = v
                    if min_dist <= 2:
                        corrected.append(best_match)
                        changed = True
                    else:
                        corrected.append(token)
        if changed:
            return " ".join(corrected)
        return None

    def search(self, query, use_expansion=False, pagerank_weight=0.0):
        """Unified search pipeline supporting:
        - Boolean, Phrase, and Wildcard query processing
        - Vector Space Model (TF-IDF Cosine similarity)
        - Rocchio/Thesaurus Query Expansion
        - PageRank graph score blending
        - Snippet-level Opinion Mining & Sentiment Analysis
        """
        if query is None or query.strip() == "":
            return {"status": "empty", "results": []}

        # Query parsing and candidate document retrieval
        candidate_docs, matched_terms = self.query_processor.process(query)

        if self.query_processor.last_error:
            return {
                "status": "query_error",
                "results": [],
                "message": self.query_processor.last_error,
            }

        if not matched_terms:
            return {"status": "only_stopwords", "results": []}

        dym = self.did_you_mean(query)

        if not candidate_docs:
            return {"status": "no_match", "results": [], "did_you_mean": dym}

        # Optional Query Expansion (Thesaurus + Pseudo-relevance feedback)
        expanded_terms_info = []
        ranking_terms = list(matched_terms)
        if use_expansion:
            ranking_terms, expanded_terms_info = self.query_expander.expand_with_thesaurus(matched_terms)

        # Vector Space Model (TF-IDF Cosine) Ranking
        ranked = self.ranker.rank(ranking_terms, candidate_docs)
        if not ranked:
            ranked = [(doc_id, 0.0) for doc_id in sorted(candidate_docs)]

        # PageRank blending: Final = (1 - w)*VSM_Score + w*PR_Score
        if pagerank_weight > 0.0:
            pr_weight = min(1.0, max(0.0, pagerank_weight))
            blended = []
            max_vsm = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
            for doc_id, vsm_score in ranked:
                norm_vsm = vsm_score / max_vsm if max_vsm > 0 else 0.0
                pr_score = self.pagerank.get_score(doc_id)
                final_score = (1.0 - pr_weight) * norm_vsm + pr_weight * pr_score
                blended.append((doc_id, final_score))
            blended.sort(key=lambda pair: pair[1], reverse=True)
            ranked = blended

        max_score = ranked[0][1] if ranked else 0.0

        results = []
        for doc_id, score in ranked:
            relative = (score / max_score * 100.0) if max_score > 0 else 0.0
            snippet = self.preview(doc_id, matched_terms)
            sentiment_info = self.sentiment_analyzer.analyze_text(snippet)

            results.append({
                "doc_id": doc_id,
                "filename": self.doc_filenames[doc_id],
                "score": round(score, 4),
                "relative": round(relative, 1),
                "preview": snippet,
                "sentiment": sentiment_info,
                "pagerank": round(self.pagerank.get_score(doc_id), 4)
            })

        return {
            "status": "ok",
            "results": results,
            "matched_terms": matched_terms,
            "expanded_terms": expanded_terms_info,
            "model": "Vector Space Model (TF-IDF)",
            "pagerank_weight": pagerank_weight,
            "did_you_mean": dym if len(results) < 3 else None
        }
