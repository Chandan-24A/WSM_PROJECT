from collections import defaultdict


class PageRank:
    """Document graph construction and PageRank computation for Shakespeare acts."""

    def __init__(self, doc_filenames, doc_texts=None, damping_factor=0.85, max_iter=100, tol=1e-6):
        self.doc_filenames = doc_filenames
        self.doc_texts = doc_texts or {}
        self.damping = damping_factor
        self.max_iter = max_iter
        self.tol = tol
        self.graph = defaultdict(set) # doc_id -> set of target doc_ids it links to
        self.in_links = defaultdict(set) # doc_id -> set of source doc_ids linking to it
        self.scores = {}
        self._build_graph()
        self.compute()

    def _parse_play_and_act(self, filename):
        # E.g. "Hamlet - ACT 1.txt" -> ("Hamlet", 1)
        import re
        m = re.search(r"^(.*?)\s*-\s*ACT\s*(\d+)", filename, re.IGNORECASE)
        if m:
            return m.group(1).strip(), int(m.group(2))
        return filename, 1

    def _build_graph(self):
        """Construct directed link graph based on:
        1. Sequential act narrative flow (Act i -> Act i+1).
        2. Climax / reference feedback links (Final Act -> Act 1).
        3. Cross-play thematic/character links (e.g. Kingship / Tragedy motif cross-references).
        """
        play_acts = defaultdict(list)
        for doc_id, filename in self.doc_filenames.items():
            play, act_num = self._parse_play_and_act(filename)
            play_acts[play].append((act_num, doc_id))

        for play, acts in play_acts.items():
            acts.sort(key=lambda x: x[0])
            for i in range(len(acts)):
                cur_id = acts[i][1]
                # Forward narrative flow
                if i + 1 < len(acts):
                    next_id = acts[i + 1][1]
                    self.graph[cur_id].add(next_id)
                # Dramatic resolution loop back to prologue/exposition
                if i == len(acts) - 1 and len(acts) > 1:
                    first_id = acts[0][1]
                    self.graph[cur_id].add(first_id)

        # Cross-play royal tragedy links between central king plays
        # King Lear, Hamlet, Henry IV, Macbeth all feature regal crisis
        for doc_id, filename in self.doc_filenames.items():
            fn_lower = filename.lower()
            if "act 3" in fn_lower or "act 1" in fn_lower: # Pivotal dramatic acts
                for other_id, other_fn in self.doc_filenames.items():
                    if doc_id != other_id and ("king" in other_fn.lower() or "hamlet" in other_fn.lower()):
                        # Add selective cross-reference edge
                        if (doc_id + other_id) % 3 == 0:
                            self.graph[doc_id].add(other_id)

        # Ensure all nodes exist in graph
        for doc_id in self.doc_filenames:
            if doc_id not in self.graph:
                self.graph[doc_id] = set()

        for src, targets in self.graph.items():
            for tgt in targets:
                self.in_links[tgt].add(src)

    def compute(self):
        """Compute PageRank scores using the standard power iteration method."""
        nodes = list(self.doc_filenames.keys())
        n = len(nodes)
        if n == 0:
            return {}

        # Initialize uniform distribution
        scores = {node: 1.0 / n for node in nodes}

        for _ in range(self.max_iter):
            new_scores = {}
            # Handle dangling nodes (nodes with out-degree 0)
            dangling_sum = sum(scores[node] for node in nodes if len(self.graph[node]) == 0)

            for node in nodes:
                incoming_sum = sum(
                    scores[src] / len(self.graph[src])
                    for src in self.in_links[node]
                    if len(self.graph[src]) > 0
                )
                new_score = (
                    (1.0 - self.damping) / n
                    + self.damping * (incoming_sum + dangling_sum / n)
                )
                new_scores[node] = new_score

            # Check convergence
            diff = sum(abs(new_scores[node] - scores[node]) for node in nodes)
            scores = new_scores
            if diff < self.tol:
                break

        # Normalize so max score is 1.0 for ease of display and blending
        max_s = max(scores.values()) if scores else 1.0
        self.scores = {node: score / max_s for node, score in scores.items()}
        return self.scores

    def get_score(self, doc_id):
        return self.scores.get(doc_id, 0.0)

    def get_graph_details(self):
        """Return graph nodes, edges, and statistics for UI presentation."""
        nodes_info = []
        for doc_id, filename in self.doc_filenames.items():
            nodes_info.append({
                "doc_id": doc_id,
                "filename": filename,
                "score": round(self.scores.get(doc_id, 0.0), 4),
                "in_degree": len(self.in_links[doc_id]),
                "out_degree": len(self.graph[doc_id])
            })
        nodes_info.sort(key=lambda x: x["score"], reverse=True)

        edges = []
        for src, targets in self.graph.items():
            for tgt in targets:
                edges.append({"source": self.doc_filenames[src], "target": self.doc_filenames[tgt]})

        return {"nodes": nodes_info, "edges": edges}
