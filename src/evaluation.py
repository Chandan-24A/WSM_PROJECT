import math


BENCHMARK_QUERIES = [
    {
        "query": "hamlet ghost father",
        "description": "Apparition of Hamlet's father on the ramparts and closet scene",
        "relevant_patterns": ["Hamlet - ACT 1", "Hamlet - ACT 3"]
    },
    {
        "query": "witch prophecy macbeth",
        "description": "Three weird sisters prophesying kingship and doom to Macbeth",
        "relevant_patterns": ["Macbeth - ACT 1", "Macbeth - ACT 4"]
    },
    {
        "query": "dagger duncan murder",
        "description": "Vision of the bloody dagger and assassination of King Duncan",
        "relevant_patterns": ["Macbeth - ACT 2"]
    },
    {
        "query": "cordelia daughters kingdom lear",
        "description": "Division of the kingdom and Cordelia's banishment and reconciliation",
        "relevant_patterns": ["King Lear - ACT 1", "King Lear - ACT 4", "King Lear - ACT 5"]
    },
    {
        "query": "falstaff honor tavern",
        "description": "Falstaff's tavern antics and catechism on military honor",
        "relevant_patterns": ["Henry IV - ACT 1", "Henry IV - ACT 2", "Henry IV - ACT 4", "Henry IV - ACT 5"]
    },
    {
        "query": "yorick skull grave",
        "description": "The graveyard scene with the skull of Yorick",
        "relevant_patterns": ["Hamlet - ACT 5"]
    }
]


class IREvaluator:
    """Graduation-level Information Retrieval Evaluation Framework:
    Precision@K, Recall@K, F1@K, Average Precision (AP), Mean Average Precision (MAP),
    Reciprocal Rank (RR), Mean Reciprocal Rank (MRR), and NDCG@K.
    """

    def __init__(self, search_engine):
        self.search_engine = search_engine

    def _is_relevant(self, filename, relevant_patterns):
        return any(pat.lower() in filename.lower() for pat in relevant_patterns)

    def evaluate_query(self, query_item, k=5):
        query = query_item["query"]
        patterns = query_item["relevant_patterns"]

        # Run search engine with Vector Space Model
        response = self.search_engine.search(query)
        results = response.get("results", [])

        # Find total relevant in entire collection for this query
        all_relevant = [
            doc_id for doc_id, fn in self.search_engine.doc_filenames.items()
            if self._is_relevant(fn, patterns)
        ]
        total_relevant = len(all_relevant)

        retrieved_k = results[:k]
        rel_retrieved = [
            1 if self._is_relevant(r["filename"], patterns) else 0
            for r in retrieved_k
        ]

        # Precision@K: Fraction of retrieved docs in top-K that are relevant
        p_at_k = sum(rel_retrieved) / k if k > 0 else 0.0

        # Recall@K: Fraction of all relevant docs that appear in top-K
        r_at_k = sum(rel_retrieved) / total_relevant if total_relevant > 0 else 0.0

        # F1-Measure
        f1_at_k = (2 * p_at_k * r_at_k / (p_at_k + r_at_k)) if (p_at_k + r_at_k) > 0 else 0.0

        # Reciprocal Rank (RR): 1 / rank of first relevant item
        rr = 0.0
        for rank, r in enumerate(results, start=1):
            if self._is_relevant(r["filename"], patterns):
                rr = 1.0 / rank
                break

        # Average Precision (AP)
        hits = 0
        sum_precisions = 0.0
        for rank, r in enumerate(results, start=1):
            if self._is_relevant(r["filename"], patterns):
                hits += 1
                sum_precisions += hits / rank
        ap = sum_precisions / total_relevant if total_relevant > 0 else 0.0

        # Discounted Cumulative Gain (DCG@K) & Ideal DCG (IDCG@K)
        dcg = 0.0
        for i, rel in enumerate(rel_retrieved, start=1):
            dcg += rel / math.log2(i + 1)

        idcg = 0.0
        for i in range(1, min(k, total_relevant) + 1):
            idcg += 1.0 / math.log2(i + 1)

        ndcg = dcg / idcg if idcg > 0 else 0.0

        return {
            "query": query,
            "description": query_item["description"],
            "total_relevant": total_relevant,
            "retrieved_count": len(results),
            "p_at_k": round(p_at_k, 4),
            "r_at_k": round(r_at_k, 4),
            "f1_at_k": round(f1_at_k, 4),
            "ap": round(ap, 4),
            "rr": round(rr, 4),
            "ndcg_at_k": round(ndcg, 4),
            "top_results": [
                {
                    "rank": idx + 1,
                    "filename": r["filename"],
                    "relevant": bool(self._is_relevant(r["filename"], patterns))
                }
                for idx, r in enumerate(retrieved_k)
            ]
        }

    def run_benchmark(self, k=5):
        """Run full evaluation suite over benchmark queries and return macro-averaged metrics."""
        per_query = []
        for q in BENCHMARK_QUERIES:
            per_query.append(self.evaluate_query(q, k=k))

        num_q = len(per_query)
        map_score = sum(q["ap"] for q in per_query) / num_q if num_q else 0.0
        mrr_score = sum(q["rr"] for q in per_query) / num_q if num_q else 0.0
        mean_p = sum(q["p_at_k"] for q in per_query) / num_q if num_q else 0.0
        mean_r = sum(q["r_at_k"] for q in per_query) / num_q if num_q else 0.0
        mean_ndcg = sum(q["ndcg_at_k"] for q in per_query) / num_q if num_q else 0.0

        return {
            "model": "Vector Space Model (TF-IDF Cosine)",
            "k": k,
            "MAP": round(map_score, 4),
            "MRR": round(mrr_score, 4),
            "mean_precision": round(mean_p, 4),
            "mean_recall": round(mean_r, 4),
            "mean_ndcg": round(mean_ndcg, 4),
            "queries": per_query
        }
