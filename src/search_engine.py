import re
from src.document_loader import load_documents
from src.indexer import InvertedIndex
from src.query_processor import QueryProcessor
from src.ranker import Ranker

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
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
    def __init__(self, documents_dir):
        self.documents_dir = documents_dir
        self.doc_filenames = {}
        self.doc_texts = {}
        self.index = None
        self.query_processor = None
        self.ranker = None

    def build_index(self):
        self.doc_filenames, self.doc_texts = load_documents(self.documents_dir)
        self.index = InvertedIndex()
        self.index.build(self.doc_texts)
        self.query_processor = QueryProcessor(self.index)
        self.ranker = Ranker(self.index)

    def preview(self, doc_id, matched_terms=None, length=250):
        text = re.sub(r"\s+", " ", self.doc_texts[doc_id]).strip()

        if matched_terms:
            text_lower = text.lower()
            match_idx = -1
            for term in matched_terms:
                idx = text_lower.find(term.lower())
                if idx != -1:
                    match_idx = idx
                    break

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
        vocab = self.index.vocabulary()
        corrected = []
        changed = False
        from src.text_processor import preprocess
        for token in tokens:
            if token in ('AND', 'OR', 'NOT', '(', ')') or '*' in token:
                corrected.append(token)
            else:
                prep = preprocess(token)
                if not prep:
                    corrected.append(token)
                    continue
                t = prep[0]
                if t in vocab:
                    corrected.append(token)
                else:
                    best_match = t
                    min_dist = 999
                    for v in vocab:
                        if abs(len(v) - len(t)) > 2: continue
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

    def search(self, query):
        if query is None or query.strip() == "":
            return {"status": "empty", "results": []}

        candidate_docs, matched_terms = self.query_processor.process(query)

        if self.query_processor.last_error:
            return {
                "status": "query_error",
                "results": [],
                "message": self.query_processor.last_error,
            }

        if not matched_terms:
            return {"status": "only_stopwords", "results": []}

        if not candidate_docs:
            dym = self.did_you_mean(query)
            return {"status": "no_match", "results": [], "did_you_mean": dym}

        ranked = self.ranker.rank(matched_terms, candidate_docs)
        # A valid Boolean query can contain only negated or ubiquitous terms,
        # which produces a zero-length TF-IDF query vector. Preserve its matches.
        if not ranked:
            ranked = [(doc_id, 0.0) for doc_id in sorted(candidate_docs)]

        max_score = ranked[0][1] if ranked else 0.0

        results = []
        for doc_id, score in ranked:
            relative = (score / max_score * 100) if max_score > 0 else 0.0
            results.append({
                "filename": self.doc_filenames[doc_id],
                "score": score,
                "relative": relative,
                "preview": self.preview(doc_id, matched_terms),
            })

        return {
            "status": "ok",
            "results": results,
            "matched_terms": matched_terms,
            "did_you_mean": self.did_you_mean(query) if len(results) < 3 else None
        }
