from collections import Counter
from src.text_processor import preprocess, STOP_WORDS


class InvertedIndex:
    """Positional inverted index preserving true token positions:
    term -> doc_id -> list of token positions.
    """

    def __init__(self):
        self.index = {}            # term -> {doc_id: [positions]}
        self.term_freq = {}        # doc_id -> Counter({term: count})
        self.content_term_freq = {}# doc_id -> Counter({term: count}) excluding stopwords
        self.doc_length = {}       # doc_id -> total token count
        self.doc_ids = []
        self.avg_doc_length = 0.0

    def build(self, doc_texts):
        total_tokens = 0
        for doc_id, text in doc_texts.items():
            tokens = preprocess(text, keep_stopwords=True)
            self.doc_ids.append(doc_id)
            self.term_freq[doc_id] = Counter(tokens)
            self.content_term_freq[doc_id] = Counter([t for t in tokens if t not in STOP_WORDS])
            self.doc_length[doc_id] = len(tokens)
            total_tokens += len(tokens)

            for position, term in enumerate(tokens):
                self.index.setdefault(term, {}).setdefault(doc_id, []).append(position)

        self.avg_doc_length = total_tokens / len(self.doc_ids) if self.doc_ids else 0.0

    def lookup(self, term):
        return set(self.index.get(term, {}))

    def vocabulary(self, include_stopwords=True):
        if include_stopwords:
            return list(self.index)
        return [t for t in self.index if t not in STOP_WORDS]

    def document_count(self):
        return len(self.doc_ids)

    def term_frequency(self, term, doc_id):
        return self.term_freq.get(doc_id, {}).get(term, 0)

    def get_positions(self, term, doc_id):
        return self.index.get(term, {}).get(doc_id, [])
