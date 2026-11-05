import re
from collections import defaultdict


class KGramIndex:
    """Character k-gram index for fast tolerant retrieval and wildcard candidate selection."""

    def __init__(self, k=3):
        self.k = k
        self.index = defaultdict(set)
        self.vocabulary = []

    def build(self, vocabulary):
        self.vocabulary = list(vocabulary)
        self.index.clear()
        for term in self.vocabulary:
            padded = f"${term}$"
            for i in range(len(padded) - self.k + 1):
                gram = padded[i:i + self.k]
                self.index[gram].add(term)

    def candidate_terms(self, pattern):
        parts = pattern.split("*")
        grams = []
        for i, part in enumerate(parts):
            if not part:
                continue
            token = part
            if i == 0:
                token = f"${part}"
            if i == len(parts) - 1:
                token = f"{token}$"
            for j in range(len(token) - self.k + 1):
                grams.append(token[j:j + self.k])

        if not grams:
            return set(self.vocabulary)

        candidate_sets = [self.index[g] for g in grams if g in self.index]
        if not candidate_sets:
            return set()

        candidates = set.intersection(*candidate_sets) if candidate_sets else set()
        return candidates


def has_wildcard(term):
    return "*" in term


def expand(pattern, vocabulary, kgram_index=None):
    """Expand a wildcard pattern against vocabulary using k-gram index filtering and regex post-check."""
    regex_text = "^" + re.escape(pattern).replace("\\*", ".*") + "$"
    regex = re.compile(regex_text)

    if kgram_index is not None and len(pattern.replace("*", "")) >= 2:
        candidates = kgram_index.candidate_terms(pattern)
        return [term for term in candidates if regex.match(term)]

    return [term for term in vocabulary if regex.match(term)]
