import math
from collections import Counter


class Ranker:
    """Graduation-level Vector Space Model (VSM) document ranking using TF-IDF Cosine Similarity."""

    def __init__(self, index):
        self.index = index
        self.idf = {}
        self.doc_norm = {}
        self._prepare()

    def _prepare(self):
        n = self.index.document_count()
        if n == 0:
            return

        # Smoothed Inverse Document Frequency: idf = ln(1 + N / df)
        # Prevents ubiquitous terms present in all N documents from yielding idf = 0
        for term, postings in self.index.index.items():
            df = len(postings)
            self.idf[term] = math.log(1.0 + (n / df))

        # Precompute L2 document vector norms over content words for Cosine Normalization
        for doc_id in self.index.doc_ids:
            total_sq = 0.0
            term_counts = self.index.content_term_freq.get(doc_id, self.index.term_freq.get(doc_id, {}))
            for term, freq in term_counts.items():
                if term in self.idf:
                    # Sublinear TF: 1 + ln(tf)
                    w = (1.0 + math.log(freq)) * self.idf[term]
                    total_sq += w * w
            self.doc_norm[doc_id] = math.sqrt(total_sq) if total_sq > 0 else 1.0

    def rank(self, query_terms, candidate_doc_ids):
        """Rank candidate documents using the Vector Space Model (TF-IDF Cosine Similarity)."""
        query_counts = Counter(query_terms)

        # Build query vector
        query_vector = {}
        for term, freq in query_counts.items():
            if term in self.idf:
                query_vector[term] = (1.0 + math.log(freq)) * self.idf[term]

        query_norm = math.sqrt(sum(w * w for w in query_vector.values()))
        if query_norm == 0:
            return [(doc_id, 0.0) for doc_id in sorted(candidate_doc_ids)]

        scores = []
        for doc_id in candidate_doc_ids:
            dot = 0.0
            for term, q_weight in query_vector.items():
                tf = self.index.term_frequency(term, doc_id)
                if tf > 0:
                    d_weight = (1.0 + math.log(tf)) * self.idf[term]
                    dot += q_weight * d_weight

            denom = query_norm * self.doc_norm.get(doc_id, 1.0)
            score = dot / denom if denom != 0 else 0.0
            scores.append((doc_id, score))

        scores.sort(key=lambda pair: pair[1], reverse=True)
        return scores
