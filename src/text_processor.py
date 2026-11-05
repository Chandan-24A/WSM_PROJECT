import re

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "had", "has", "have", "he", "her", "his", "i", "in", "is", "it", "its",
    "me", "my", "no", "nor", "not", "o", "of", "on", "or", "our", "s", "she",
    "so", "than", "that", "the", "thee", "their", "them", "then", "there",
    "these", "they", "this", "thou", "thy", "to", "too", "us", "was", "we",
    "were", "what", "when", "which", "who", "will", "with", "would", "you",
    "your", "ye", "hath", "doth", "shall", "upon"
}


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s*]", " ", text)
    return text


def tokenize(text):
    return text.split()


def remove_stop_words(tokens):
    return [t for t in tokens if t not in STOP_WORDS]


def stem_word(word):
    """Rule-based suffix stemmer (Step 1 of Porter Stemmer) for morphological normalization."""
    if len(word) <= 3:
        return word
    # Step 1a: plurals and -ed or -ing
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies"):
        return word[:-2]
    if word.endswith("ss"):
        return word
    if word.endswith("s") and not word.endswith("us") and not word.endswith("is"):
        return word[:-1]
    if word.endswith("eed"):
        return word[:-1]
    if (word.endswith("ed") or word.endswith("ing")) and len(word) > 4:
        stem = word[:-2] if word.endswith("ed") else word[:-3]
        if len(stem) >= 3:
            return stem
    return word


def preprocess(text, keep_stopwords=False, stem=False):
    """Normalize and tokenize text.
    
    If keep_stopwords is False, filters out stop words.
    If True, keeps all tokens for exact phrase indexing.
    If stem is True, applies suffix stemming.
    """
    text = normalize(text)
    tokens = tokenize(text)
    if not keep_stopwords:
        tokens = remove_stop_words(tokens)
    if stem:
        tokens = [stem_word(t) for t in tokens]
    return tokens
