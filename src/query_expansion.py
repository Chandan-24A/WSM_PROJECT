from collections import Counter
from src.text_processor import STOP_WORDS, preprocess

SHAKESPEARE_THESAURUS = {
    "king": ["monarch", "sovereign", "majesty", "ruler", "crown"],
    "queen": ["monarch", "lady", "majesty", "royalty"],
    "crown": ["throne", "sceptre", "coronet", "reign"],
    "murder": ["slain", "blood", "kill", "dagger", "death", "slaughter"],
    "ghost": ["spirit", "apparition", "phantom", "spectre"],
    "madness": ["lunacy", "insanity", "mad", "distraction"],
    "witch": ["weird", "prophecy", "sorcery", "hags"],
    "sword": ["blade", "rapier", "steel", "weapon"],
    "treason": ["traitor", "betrayal", "conspiracy", "rebellion"],
    "honor": ["glory", "valiant", "noble", "dignity"],
    "father": ["parent", "sire", "lineage"],
    "death": ["grave", "perish", "mortality", "doom"],
    "love": ["affection", "passion", "heart", "beloved"],
    "war": ["battle", "conflict", "arms", "soldier"],
    "fear": ["terror", "dread", "horror", "fright"]
}


class QueryExpander:
    """Query expansion using pseudo-relevance feedback (Rocchio) and thesaurus expansion."""

    def __init__(self, index, ranker):
        self.index = index
        self.ranker = ranker

    def expand_with_thesaurus(self, query_terms, max_additions=2):
        """Expand terms using curated Shakespearean semantic associations."""
        expanded_terms = list(query_terms)
        added = []

        for term in query_terms:
            t_lower = term.lower()
            if t_lower in SHAKESPEARE_THESAURUS:
                for syn in SHAKESPEARE_THESAURUS[t_lower]:
                    # Only add if the synonym exists in the corpus vocabulary
                    if syn in self.index.index and syn not in expanded_terms and syn not in STOP_WORDS:
                        expanded_terms.append(syn)
                        added.append(syn)
                        if len(added) >= max_additions:
                            break
            if len(added) >= max_additions:
                break

        return expanded_terms, added

    def expand_with_rocchio(self, original_terms, top_doc_ids, num_terms=2):
        """Pseudo-relevance feedback: extract high-weight informative terms from top-ranked documents."""
        if not top_doc_ids:
            return original_terms, []

        candidate_scores = Counter()
        for doc_id in top_doc_ids[:3]:
            for term, count in self.index.content_term_freq[doc_id].items():
                if term not in original_terms and term not in STOP_WORDS and len(term) > 2:
                    idf = self.ranker.idf.get(term, 0.0)
                    candidate_scores[term] += count * idf

        most_relevant = [term for term, _ in candidate_scores.most_common(num_terms)]
        expanded = original_terms + most_relevant
        return expanded, most_relevant
