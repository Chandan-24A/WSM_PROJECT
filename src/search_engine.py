import re

from src.document_loader import load_documents
from src.indexer import InvertedIndex
from src.query_processor import QueryProcessor
from src.ranker import Ranker


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

    def preview(self, doc_id, matched_terms=None, length=200):
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

    def search(self, query):
        if query is None or query.strip() == "":
            return {"status": "empty", "results": []}

        candidate_docs, matched_terms = self.query_processor.process(query)

        if not matched_terms:
            return {"status": "only_stopwords", "results": []}

        if not candidate_docs:
            return {"status": "no_match", "results": []}

        ranked = self.ranker.rank(matched_terms, candidate_docs)

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

        return {"status": "ok", "results": results}
