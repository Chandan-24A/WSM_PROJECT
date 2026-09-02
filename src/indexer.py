from collections import Counter

from src.text_processor import preprocess


class InvertedIndex:
    """In-memory positional inverted index: term -> document -> token positions."""

    def __init__(self):
        self.index = {}
        self.term_freq = {}
        self.doc_length = {}
        self.doc_ids = []

    def build(self, doc_texts):
        for doc_id, text in doc_texts.items():
            tokens = preprocess(text)
            self.doc_ids.append(doc_id)
            self.term_freq[doc_id] = Counter(tokens)
            self.doc_length[doc_id] = len(tokens)
            for position, term in enumerate(tokens):
                self.index.setdefault(term, {}).setdefault(doc_id, []).append(position)

    def lookup(self, term):
        return set(self.index.get(term, {}))

    def vocabulary(self):
        return list(self.index)

    def document_count(self):
        return len(self.doc_ids)

    def term_frequency(self, term, doc_id):
        return self.term_freq.get(doc_id, {}).get(term, 0)

    def get_positions(self, term, doc_id):
        return self.index.get(term, {}).get(doc_id, [])
