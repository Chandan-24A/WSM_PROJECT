import re
from src.text_processor import preprocess, normalize
from src.wildcard import expand, has_wildcard


class QueryProcessor:
    """Parse and evaluate Boolean, wildcard, and quoted phrase queries."""

    OPERATORS = {"AND", "OR", "NOT"}
    PRECEDENCE = {"NOT": 3, "AND": 2, "OR": 1}

    def __init__(self, index, kgram_index=None):
        self.index = index
        self.kgram_index = kgram_index
        self.last_error = None

    def _tokenize_query(self, query):
        raw_tokens = re.findall(r'"[^"\n]*"|\(|\)|[^\s()]+', query)
        tokens = []
        for raw in raw_tokens:
            upper = raw.upper()
            if raw in ("(", ")"):
                token = raw
            elif upper in self.OPERATORS:
                token = upper
            elif raw.startswith('"') and raw.endswith('"'):
                token = ("PHRASE", raw[1:-1])
            else:
                token = ("TERM", raw)
            if tokens and self._ends_operand(tokens[-1]) and self._starts_operand(token):
                tokens.append("AND")
            tokens.append(token)
        return tokens

    @staticmethod
    def _ends_operand(token):
        return token == ")" or isinstance(token, tuple)

    @staticmethod
    def _starts_operand(token):
        return token == "(" or token == "NOT" or isinstance(token, tuple)

    def _to_postfix(self, tokens):
        output, operators = [], []
        expecting_operand = True
        for token in tokens:
            if isinstance(token, tuple):
                if not expecting_operand:
                    raise ValueError("Missing Boolean operator between terms")
                output.append(token)
                expecting_operand = False
            elif token == "(":
                if not expecting_operand:
                    raise ValueError("Missing operator before opening parenthesis")
                operators.append(token)
            elif token == ")":
                if expecting_operand:
                    raise ValueError("Missing term before closing parenthesis")
                while operators and operators[-1] != "(":
                    output.append(operators.pop())
                if not operators:
                    raise ValueError("Unmatched closing parenthesis")
                operators.pop()
                expecting_operand = False
            else:
                if token != "NOT" and expecting_operand:
                    raise ValueError(f"Expected a term before {token}")
                while (operators and operators[-1] != "(" and
                       (self.PRECEDENCE[operators[-1]] > self.PRECEDENCE[token] or
                        (self.PRECEDENCE[operators[-1]] == self.PRECEDENCE[token] and token != "NOT"))):
                    output.append(operators.pop())
                operators.append(token)
                expecting_operand = True
        if expecting_operand and tokens:
            raise ValueError("Query cannot end with an operator")
        while operators:
            operator = operators.pop()
            if operator == "(":
                raise ValueError("Unmatched opening parenthesis")
            output.append(operator)
        return output

    def _term_documents(self, term, matched_terms):
        cleaned = normalize(term).strip()
        if not cleaned or cleaned.strip("*") == "":
            return set()

        if has_wildcard(cleaned):
            expansions = expand(cleaned, self.index.vocabulary(include_stopwords=True), self.kgram_index)
            matched_terms.extend(expansions)
            return set().union(*(self.index.lookup(item) for item in expansions)) if expansions else set()

        tokens = preprocess(cleaned, keep_stopwords=False)
        if not tokens:
            # Check if it's a stopword present in vocabulary
            if cleaned in self.index.index:
                # Recognized as stop word
                pass
            return set()

        normalized = tokens[0]
        matched_terms.append(normalized)
        return self.index.lookup(normalized)

    def _positions_for(self, term):
        cleaned = normalize(term).strip()
        terms = expand(cleaned, self.index.vocabulary(include_stopwords=True), self.kgram_index) if has_wildcard(cleaned) else [cleaned]
        positions = {}
        for item in terms:
            for doc_id in self.index.lookup(item):
                positions.setdefault(doc_id, set()).update(self.index.get_positions(item, doc_id))
        return positions, terms

    def _phrase_documents(self, phrase, matched_terms):
        # Keep all words in phrase to preserve original word positions
        terms = preprocess(phrase, keep_stopwords=True)
        if not terms:
            return set()
        position_maps = []
        for term in terms:
            positions, expansions = self._positions_for(term)
            matched_terms.extend([t for t in expansions if t not in matched_terms])
            if not positions:
                return set()
            position_maps.append(positions)

        candidate_docs = set(position_maps[0])
        for position_map in position_maps[1:]:
            candidate_docs &= set(position_map)

        matches = set()
        for doc_id in candidate_docs:
            possible_positions = position_maps[0][doc_id]
            for position_map in position_maps[1:]:
                next_positions = position_map[doc_id]
                possible_positions = {pos + 1 for pos in possible_positions if pos + 1 in next_positions}
                if not possible_positions:
                    break
            if possible_positions:
                matches.add(doc_id)
        return matches

    def _evaluate_operand(self, operand, matched_terms):
        kind, value = operand
        return self._phrase_documents(value, matched_terms) if kind == "PHRASE" else self._term_documents(value, matched_terms)

    def process(self, query):
        self.last_error = None
        matched_terms = []
        try:
            tokens = self._tokenize_query(query)
            if not tokens:
                return set(), []

            postfix = self._to_postfix(tokens)
            if not postfix:
                return set(), matched_terms

            stack = []
            all_docs = set(self.index.doc_ids)
            for token in postfix:
                if isinstance(token, tuple):
                    stack.append(self._evaluate_operand(token, matched_terms))
                elif token == "NOT":
                    if not stack:
                        raise ValueError("Missing operand for NOT")
                    stack.append(all_docs - stack.pop())
                else:
                    if len(stack) < 2:
                        raise ValueError(f"Missing operand for {token}")
                    right, left = stack.pop(), stack.pop()
                    stack.append(left & right if token == "AND" else left | right)
            if len(stack) != 1:
                raise ValueError("Malformed query")
            return stack[0], matched_terms
        except (IndexError, ValueError) as error:
            self.last_error = str(error)
            return set(), []
