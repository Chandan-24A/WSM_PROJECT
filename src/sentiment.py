import re
from collections import Counter

POSITIVE_LEXICON = {
    "noble": 2.0, "grace": 2.0, "honor": 2.2, "virtue": 2.0, "fair": 1.5,
    "valiant": 2.5, "gentle": 1.5, "love": 2.5, "triumph": 2.0, "sweet": 1.5,
    "heaven": 2.0, "friend": 1.8, "blessed": 2.0, "praise": 1.8, "peace": 2.0,
    "joy": 2.2, "glory": 2.0, "wisdom": 1.8, "kind": 1.5, "good": 1.5,
    "true": 1.5, "loyal": 2.0, "brave": 2.0, "beauty": 2.0, "splendor": 2.0,
    "happy": 2.0, "mercy": 2.2, "divine": 2.2, "pure": 1.8, "bright": 1.5,
    "courage": 2.0, "hope": 1.8, "fellow": 1.0, "dear": 1.5, "pleasure": 1.8
}

NEGATIVE_LEXICON = {
    "treason": 3.0, "villain": 2.8, "dagger": 2.2, "murder": 3.2, "woe": 2.2,
    "grief": 2.2, "foul": 2.5, "horror": 2.8, "bloody": 2.8, "death": 2.5,
    "tyrant": 3.0, "curse": 2.4, "poison": 3.0, "hell": 2.5, "hate": 2.5,
    "sorrow": 2.2, "plague": 2.6, "traitor": 3.0, "vile": 2.6, "dread": 2.2,
    "false": 2.0, "fatal": 2.8, "cruel": 2.5, "doom": 2.5, "rage": 2.0,
    "shame": 2.2, "slaughter": 3.0, "bleed": 2.4, "guilt": 2.4, "sin": 2.5,
    "pain": 2.0, "weep": 1.8, "rot": 2.2, "monstrous": 2.8, "evil": 2.8
}

NEGATORS = {"not", "never", "no", "nor", "neither", "scant", "without"}
INTENSIFIERS = {"very", "most", "exceeding", "mighty", "deeply", "too", "so"}


class SentimentAnalyzer:
    """Valence-based Sentiment & Opinion Mining Engine tailored for early modern dramatic texts."""

    def analyze_text(self, text):
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if not words:
            return {
                "compound": 0.0,
                "label": "Neutral",
                "pos_score": 0.0,
                "neg_score": 0.0,
                "pos_words": [],
                "neg_words": []
            }

        pos_total = 0.0
        neg_total = 0.0
        pos_words_found = []
        neg_words_found = []

        for i, word in enumerate(words):
            # Check for negation window of 2 preceding words
            negated = False
            for j in range(max(0, i - 2), i):
                if words[j] in NEGATORS:
                    negated = True
                    break

            multiplier = 1.0
            if i > 0 and words[i - 1] in INTENSIFIERS:
                multiplier = 1.5

            if word in POSITIVE_LEXICON:
                weight = POSITIVE_LEXICON[word] * multiplier
                if negated:
                    neg_total += weight
                    neg_words_found.append(f"not {word}")
                else:
                    pos_total += weight
                    pos_words_found.append(word)

            elif word in NEGATIVE_LEXICON:
                weight = NEGATIVE_LEXICON[word] * multiplier
                if negated:
                    pos_total += weight * 0.75 # Weakened negation
                    pos_words_found.append(f"not {word}")
                else:
                    neg_total += weight
                    neg_words_found.append(word)

        total_words = len(words)
        normalized_pos = pos_total / (total_words + 1)
        normalized_neg = neg_total / (total_words + 1)

        diff = pos_total - neg_total
        # Compound score bounded in [-1.0, 1.0] using hyperbolic tangent scaling
        import math
        compound = math.tanh(diff / 6.0)

        if compound >= 0.15:
            label = "Positive"
        elif compound <= -0.15:
            label = "Negative"
        else:
            label = "Neutral"

        return {
            "compound": round(compound, 3),
            "label": label,
            "pos_score": round(normalized_pos, 4),
            "neg_score": round(normalized_neg, 4),
            "pos_words": [w for w, _ in Counter(pos_words_found).most_common(5)],
            "neg_words": [w for w, _ in Counter(neg_words_found).most_common(5)]
        }

    def analyze_corpus(self, doc_filenames, doc_texts):
        """Analyze sentiment across all corpus documents and group by play."""
        doc_sentiments = []
        play_sentiments = {}

        for doc_id, filename in doc_filenames.items():
            text = doc_texts.get(doc_id, "")
            analysis = self.analyze_text(text)
            play_name = filename.split("-")[0].strip() if "-" in filename else filename

            item = {
                "doc_id": doc_id,
                "filename": filename,
                "play": play_name,
                "compound": analysis["compound"],
                "label": analysis["label"],
                "pos_words": analysis["pos_words"],
                "neg_words": analysis["neg_words"]
            }
            doc_sentiments.append(item)

            if play_name not in play_sentiments:
                play_sentiments[play_name] = []
            play_sentiments[play_name].append(analysis["compound"])

        play_averages = {
            play: round(sum(scores) / len(scores), 3)
            for play, scores in play_sentiments.items()
        }

        return {
            "documents": doc_sentiments,
            "play_averages": play_averages
        }

    def entity_opinion_mining(self, entity_name, doc_texts):
        """Extract and score opinions/sentiments in sentences mentioning a specific character."""
        sentences = []
        entity_lower = entity_name.lower().strip()
        if not entity_lower:
            return {"entity": entity_name, "count": 0, "avg_compound": 0.0, "opinions": []}

        for text in doc_texts.values():
            raw_sentences = re.split(r"[.\n!?]+", text)
            for s in raw_sentences:
                if re.search(r"\b" + re.escape(entity_lower) + r"\b", s, re.IGNORECASE):
                    s_clean = s.strip()
                    if 15 < len(s_clean) < 300:
                        analysis = self.analyze_text(s_clean)
                        sentences.append({
                            "sentence": s_clean,
                            "compound": analysis["compound"],
                            "label": analysis["label"]
                        })

        if not sentences:
            return {"entity": entity_name, "count": 0, "avg_compound": 0.0, "opinions": []}

        avg_compound = round(sum(s["compound"] for s in sentences) / len(sentences), 3)
        return {
            "entity": entity_name,
            "count": len(sentences),
            "avg_compound": avg_compound,
            "opinions": sentences[:10]
        }
