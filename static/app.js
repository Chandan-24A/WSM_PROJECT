document.addEventListener("DOMContentLoaded", () => {
  // Application State
  let rawSearchResults = [];
  let filteredSearchResults = [];
  let currentMatchedTerms = [];
  let currentPage = 0;
  let activePlayFilter = "all";
  const resultsPerPage = 5;

  // Search DOM Elements
  const searchForm = document.getElementById("search-form");
  const searchInput = document.getElementById("search-input");
  const clearSearchBtn = document.getElementById("clear-search-btn");
  const autocompleteDropdown = document.getElementById("autocomplete-dropdown");
  const expansionToggle = document.getElementById("expansion-toggle");
  const prWeightSlider = document.getElementById("pr-weight-slider");
  const prWeightLabel = document.getElementById("pr-weight-label");

  // Results DOM Elements
  const searchResultsSection = document.getElementById("search-results-section");
  const resultsCardContainer = document.getElementById("results-card-container");
  const resultsCountBadge = document.getElementById("results-count-badge");
  const emptySearchPlaceholder = document.getElementById("empty-search-placeholder");
  const dymBanner = document.getElementById("dym-banner");
  const dymLinkBtn = document.getElementById("dym-link-btn");
  const expansionInfoBanner = document.getElementById("expansion-info-banner");
  const expansionTermsText = document.getElementById("expansion-terms-text");
  const pagePrevBtn = document.getElementById("page-prev-btn");
  const pageNextBtn = document.getElementById("page-next-btn");
  const paginationStatus = document.getElementById("pagination-status");
  const playFilterContainer = document.getElementById("play-filter-container");

  // Reader Dialog Elements
  const docReaderDialog = document.getElementById("doc-reader-dialog");
  const dialogCloseBtn = document.getElementById("dialog-close-btn");
  const dialogActTitle = document.getElementById("dialog-act-title");
  const dialogActMeta = document.getElementById("dialog-act-meta");
  const dialogRawContent = document.getElementById("dialog-raw-content");
  const dialogFilterInput = document.getElementById("dialog-filter-input");
  let currentDialogFullText = "";

  // Toast
  const appToast = document.getElementById("app-toast");

  function showToast(message, duration = 3000) {
    appToast.textContent = message;
    appToast.classList.remove("hidden");
    setTimeout(() => {
      appToast.classList.add("hidden");
    }, duration);
  }

  // Navigation Tab Management
  const navBtns = document.querySelectorAll(".nav-btn");
  const tabViews = document.querySelectorAll(".tab-view");

  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      navBtns.forEach(b => b.classList.remove("active"));
      tabViews.forEach(v => v.classList.remove("active"));

      btn.classList.add("active");
      const targetView = document.getElementById(targetTab);
      if (targetView) targetView.classList.add("active");

      // Lazy Data Loaders
      if (targetTab === "tab-pagerank") loadPageRankData();
      if (targetTab === "tab-sentiment") loadSentimentData();
      if (targetTab === "tab-corpus") loadCorpusData();
    });
  });

  // PageRank Weight Slider Update
  prWeightSlider.addEventListener("input", (e) => {
    const pct = Math.round(parseFloat(e.target.value) * 100);
    prWeightLabel.textContent = `${pct}%`;
  });

  // Search Input Clear & Autocomplete
  searchInput.addEventListener("input", () => {
    clearSearchBtn.style.display = searchInput.value ? "block" : "none";
    requestAutocomplete(searchInput.value);
  });

  clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    clearSearchBtn.style.display = "none";
    autocompleteDropdown.classList.add("hidden");
    searchInput.focus();
  });

  // Shortcut key '/' focuses search bar
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== searchInput && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      const searchNav = document.querySelector('[data-tab="tab-search"]');
      if (searchNav) searchNav.click();
      searchInput.focus();
    }
  });

  // Quick Preset Sample Chips
  document.querySelectorAll(".sample-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const queryText = chip.getAttribute("data-q");
      searchInput.value = queryText;
      clearSearchBtn.style.display = "block";
      autocompleteDropdown.classList.add("hidden");
      executeRetrieval(queryText);
    });
  });

  // Search Form Submit
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (query) {
      autocompleteDropdown.classList.add("hidden");
      executeRetrieval(query);
    }
  });

  // Autocomplete Suggestions
  async function requestAutocomplete(prefix) {
    const term = prefix.trim();
    if (term.length < 2 || term.includes(" ") || term.includes('"')) {
      autocompleteDropdown.classList.add("hidden");
      return;
    }
    try {
      const res = await fetch(`/api/suggest?q=${encodeURIComponent(term)}`);
      const data = await res.json();
      if (data.suggestions && data.suggestions.length > 0) {
        autocompleteDropdown.innerHTML = data.suggestions
          .map(word => `<div class="autocomplete-item"><span>🔍</span> ${escapeHtml(word)}</div>`)
          .join("");
        autocompleteDropdown.classList.remove("hidden");

        autocompleteDropdown.querySelectorAll(".autocomplete-item").forEach(item => {
          item.addEventListener("click", () => {
            const chosen = item.textContent.replace("🔍", "").trim();
            searchInput.value = chosen;
            autocompleteDropdown.classList.add("hidden");
            executeRetrieval(chosen);
          });
        });
      } else {
        autocompleteDropdown.classList.add("hidden");
      }
    } catch {
      autocompleteDropdown.classList.add("hidden");
    }
  }

  document.addEventListener("click", (e) => {
    if (!searchForm.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
      autocompleteDropdown.classList.add("hidden");
    }
  });

  // Core Search Execution
  async function executeRetrieval(query) {
    const expand = expansionToggle.checked ? "1" : "0";
    const prWeight = prWeightSlider.value;

    searchResultsSection.classList.remove("hidden");
    emptySearchPlaceholder.classList.add("hidden");
    resultsCardContainer.innerHTML = `<div class="table-empty-msg">Searching documents with Vector Space Model...</div>`;
    dymBanner.classList.add("hidden");
    expansionInfoBanner.classList.add("hidden");

    try {
      const url = `/api/search?q=${encodeURIComponent(query)}&expand=${expand}&pagerank=${prWeight}`;
      const res = await fetch(url);
      const data = await res.json();

      handleRetrievalResponse(data, query);
    } catch (err) {
      resultsCardContainer.innerHTML = `<div class="result-doc-card" style="color:var(--danger)">Error querying retrieval engine. Please ensure Python server is active.</div>`;
    }
  }

  function handleRetrievalResponse(data, query) {
    if (data.status === "empty") {
      resultsCountBadge.textContent = "Please enter a search query above.";
      resultsCardContainer.innerHTML = "";
      return;
    }
    if (data.status === "query_error") {
      resultsCountBadge.textContent = `Invalid Boolean syntax: ${data.message || "Query parse error"}`;
      resultsCardContainer.innerHTML = "";
      return;
    }
    if (data.status === "only_stopwords") {
      resultsCountBadge.textContent = "Query contains only stop words. Try entering more distinctive terms.";
      resultsCardContainer.innerHTML = "";
      return;
    }
    if (data.status === "no_match") {
      resultsCountBadge.textContent = `No matching documents found for '${query}'.`;
      resultsCardContainer.innerHTML = "";
      if (data.did_you_mean) {
        showDidYouMean(data.did_you_mean);
      }
      return;
    }

    // Success response
    rawSearchResults = data.results || [];
    currentMatchedTerms = data.matched_terms || [];
    currentPage = 0;
    activePlayFilter = "all";

    // Reset Play filter pills
    document.querySelectorAll(".filter-pill").forEach(p => {
      p.classList.toggle("active", p.getAttribute("data-filter") === "all");
    });

    resultsCountBadge.textContent = `Found ${rawSearchResults.length} relevant act(s) for '${query}'`;

    if (data.did_you_mean) {
      showDidYouMean(data.did_you_mean);
    }

    if (data.expanded_terms && data.expanded_terms.length > 0) {
      expansionTermsText.textContent = data.expanded_terms.join(", ");
      expansionInfoBanner.classList.remove("hidden");
    }

    applyPlayFilter();
  }

  function showDidYouMean(suggestedQuery) {
    dymLinkBtn.textContent = suggestedQuery;
    dymBanner.classList.remove("hidden");
    dymLinkBtn.onclick = (e) => {
      e.preventDefault();
      searchInput.value = suggestedQuery;
      executeRetrieval(suggestedQuery);
    };
  }

  // Play Filtering Logic
  playFilterContainer.querySelectorAll(".filter-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      playFilterContainer.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activePlayFilter = pill.getAttribute("data-filter");
      currentPage = 0;
      applyPlayFilter();
    });
  });

  function applyPlayFilter() {
    if (activePlayFilter === "all") {
      filteredSearchResults = rawSearchResults;
    } else {
      filteredSearchResults = rawSearchResults.filter(item => 
        item.filename.toLowerCase().includes(activePlayFilter.toLowerCase())
      );
    }
    resultsCountBadge.textContent = `Displaying ${filteredSearchResults.length} of ${rawSearchResults.length} act(s)`;
    renderResultsPage();
  }

  // Render Paginated Results
  function renderResultsPage() {
    const total = filteredSearchResults.length;
    const totalPages = Math.ceil(total / resultsPerPage) || 1;
    const startIdx = currentPage * resultsPerPage;
    const endIdx = Math.min(startIdx + resultsPerPage, total);
    const pageItems = filteredSearchResults.slice(startIdx, endIdx);

    paginationStatus.textContent = `Page ${currentPage + 1} of ${totalPages} (${total} total)`;
    pagePrevBtn.disabled = currentPage === 0;
    pageNextBtn.disabled = endIdx >= total;

    if (pageItems.length === 0) {
      resultsCardContainer.innerHTML = "<p class='table-empty-msg'>No documents matching the active filter.</p>";
      return;
    }

    resultsCardContainer.innerHTML = pageItems.map((item, idx) => {
      const overallRank = startIdx + idx + 1;
      const highlightedSnippet = highlightMatchingTerms(item.preview, currentMatchedTerms);
      const sent = item.sentiment || { label: "Neutral", compound: 0.0 };
      const sentPillClass = sent.label === "Positive" ? "pill-pos" : (sent.label === "Negative" ? "pill-neg" : "pill-neu");

      return `
        <article class="result-doc-card">
          <div class="card-header-line">
            <div class="card-title-wrap">
              <span class="rank-index">${overallRank}</span>
              <span class="act-title">${escapeHtml(item.filename)}</span>
            </div>
            <div class="pill-group">
              <span class="meta-pill pill-relevance">Relevance: ${item.relative}% (VSM: ${item.score})</span>
              <span class="meta-pill pill-pr" title="PageRank eigenvector score">PR: ${item.pagerank}</span>
              <span class="meta-pill ${sentPillClass}" title="Sentiment compound valence">Sentiment: ${sent.label} (${sent.compound})</span>
            </div>
          </div>
          <div class="relevance-track">
            <div class="relevance-fill" style="width: ${Math.max(4, item.relative)}%;"></div>
          </div>
          <div class="snippet-box">
            "${highlightedSnippet}"
          </div>
          <div class="card-footer-line">
            <span>Corpus ID: #${item.doc_id}</span>
            <button class="btn-read-act" data-docid="${item.doc_id}">Read Full Act ↗</button>
          </div>
        </article>
      `;
    }).join("");

    // Hook read document triggers
    document.querySelectorAll(".btn-read-act").forEach(btn => {
      btn.addEventListener("click", () => {
        openDocumentDialog(btn.getAttribute("data-docid"));
      });
    });
  }

  // Pagination Event Handlers
  pagePrevBtn.addEventListener("click", () => {
    if (currentPage > 0) {
      currentPage--;
      renderResultsPage();
      searchResultsSection.scrollIntoView({ behavior: "smooth" });
    }
  });

  pageNextBtn.addEventListener("click", () => {
    if ((currentPage + 1) * resultsPerPage < filteredSearchResults.length) {
      currentPage++;
      renderResultsPage();
      searchResultsSection.scrollIntoView({ behavior: "smooth" });
    }
  });

  // Query Term Highlighting
  function highlightMatchingTerms(text, terms) {
    if (!text) return "";
    let safe = escapeHtml(text);
    if (!terms || terms.length === 0) return safe;

    terms.forEach(term => {
      if (term.length < 2) return;
      const cleanTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const reg = new RegExp(`(${cleanTerm})`, 'gi');
      safe = safe.replace(reg, `<mark class="matched-term">$1</mark>`);
    });
    return safe;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Modal Dialog Document Viewer
  async function openDocumentDialog(docId) {
    dialogActTitle.textContent = "Loading dramatic act...";
    dialogActMeta.textContent = "";
    dialogRawContent.textContent = "Retrieving text...";
    dialogFilterInput.value = "";
    docReaderDialog.showModal();

    try {
      const res = await fetch(`/api/document/${docId}`);
      const data = await res.json();
      currentDialogFullText = data.text;
      dialogActTitle.textContent = data.filename;
      dialogActMeta.innerHTML = `
        <span class="meta-pill pill-relevance">${data.total_words} words</span>
        <span class="meta-pill pill-pr">PageRank: ${data.pagerank}</span>
        <span class="meta-pill ${data.sentiment.label === 'Positive' ? 'pill-pos' : (data.sentiment.label === 'Negative' ? 'pill-neg' : 'pill-neu')}">
          Sentiment: ${data.sentiment.label} (${data.sentiment.compound})
        </span>
      `;
      dialogRawContent.textContent = data.text;
    } catch {
      dialogRawContent.textContent = "Error loading document.";
    }
  }

  // In-document Search Filter within Reader
  dialogFilterInput.addEventListener("input", (e) => {
    const term = e.target.value.trim();
    if (!term || !currentDialogFullText) {
      dialogRawContent.textContent = currentDialogFullText;
      return;
    }
    const clean = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const reg = new RegExp(`(${clean})`, 'gi');
    const highlighted = escapeHtml(currentDialogFullText).replace(reg, `<mark class="matched-term">$1</mark>`);
    dialogRawContent.innerHTML = highlighted;
  });

  dialogCloseBtn.addEventListener("click", () => docReaderDialog.close());
  docReaderDialog.addEventListener("click", (e) => {
    if (e.target === docReaderDialog) docReaderDialog.close();
  });

  // TAB 2: PageRank Loader
  async function loadPageRankData() {
    const tbody = document.getElementById("pr-table-rows");
    try {
      const res = await fetch("/api/pagerank");
      const data = await res.json();
      if (data.nodes && data.nodes.length > 0) {
        document.getElementById("top-pr-name").textContent = data.nodes[0].filename;
        tbody.innerHTML = data.nodes.map((node, i) => `
          <tr>
            <td><strong>#${i + 1}</strong></td>
            <td><strong>${escapeHtml(node.filename)}</strong></td>
            <td><span class="meta-pill pill-pr">${node.score}</span></td>
            <td>${node.in_degree} incoming</td>
            <td>${node.out_degree} outgoing</td>
            <td><button class="btn-read-act" onclick="document.dispatchEvent(new CustomEvent('openActFromTable', {detail: ${node.doc_id}}))">View Act</button></td>
          </tr>
        `).join("");
      }
    } catch {
      tbody.innerHTML = `<tr><td colspan="6" class="table-empty-msg" style="color:var(--danger)">Failed to load PageRank data.</td></tr>`;
    }
  }

  document.getElementById("recompute-pr-btn").addEventListener("click", () => {
    showToast("Recomputing PageRank power iteration graph...");
    loadPageRankData();
  });
  document.addEventListener("openActFromTable", (e) => openDocumentDialog(e.detail));

  // TAB 3: Opinion & Sentiment Loader
  async function loadSentimentData() {
    const grid = document.getElementById("play-sentiment-display");
    try {
      const res = await fetch("/api/sentiment");
      const data = await res.json();

      if (data.play_averages) {
        grid.innerHTML = Object.entries(data.play_averages).map(([play, score]) => {
          const isPos = score > 0.05;
          const isNeg = score < -0.05;
          const pillClass = isPos ? "pill-pos" : (isNeg ? "pill-neg" : "pill-neu");
          const moodDesc = isPos ? "Tending Heroic / Regal" : (isNeg ? "Tending Tragic / Dark Conflict" : "Dramatic Equilibrium");
          return `
            <div class="play-metric-box">
              <div class="play-metric-title">${escapeHtml(play)}</div>
              <div style="margin: 8px 0;">
                <span class="meta-pill ${pillClass}">Valence: ${score}</span>
              </div>
              <p class="card-caption" style="font-size:0.84rem;">${moodDesc}</p>
            </div>
          `;
        }).join("");
      }
    } catch {
      grid.innerHTML = `<p class="table-empty-msg" style="color:var(--danger)">Error loading sentiment metrics.</p>`;
    }
  }

  // Character Opinion Miner Tool
  const charQueryInput = document.getElementById("character-query-input");
  const btnRunMiner = document.getElementById("btn-run-miner");
  const minerFeed = document.getElementById("miner-results-feed");

  btnRunMiner.addEventListener("click", runCharacterOpinionMining);

  document.querySelectorAll(".entity-pill").forEach(chip => {
    chip.addEventListener("click", () => {
      charQueryInput.value = chip.getAttribute("data-name");
      runCharacterOpinionMining();
    });
  });

  async function runCharacterOpinionMining() {
    const name = charQueryInput.value.trim();
    if (!name) return;
    minerFeed.innerHTML = "<p class='table-empty-msg'>Mining dialogue opinions across 19 dramatic acts...</p>";

    try {
      const res = await fetch(`/api/sentiment/entity?name=${encodeURIComponent(name)}`);
      const data = await res.json();

      if (!data.opinions || data.opinions.length === 0) {
        minerFeed.innerHTML = `<p class="card-caption">No dialogue mentions found for '${escapeHtml(name)}'.</p>`;
        return;
      }

      const valenceClass = data.avg_compound >= 0.1 ? "pill-pos" : (data.avg_compound <= -0.1 ? "pill-neg" : "pill-neu");

      minerFeed.innerHTML = `
        <div style="margin-bottom: 14px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
          <strong>Found ${data.count} dialogue reference(s)</strong>
          <span class="meta-pill ${valenceClass}">Average Valence: ${data.avg_compound}</span>
        </div>
        <div class="miner-results-feed">
          ${data.opinions.map(op => `
            <div class="opinion-bubble">
              <div class="opinion-quote">"${escapeHtml(op.sentence)}"</div>
              <span class="meta-pill ${op.label === 'Positive' ? 'pill-pos' : (op.label === 'Negative' ? 'pill-neg' : 'pill-neu')}">
                ${op.label} (${op.compound})
              </span>
            </div>
          `).join("")}
        </div>
      `;
    } catch {
      minerFeed.innerHTML = `<p class="table-empty-msg" style="color:var(--danger)">Error executing opinion mining.</p>`;
    }
  }

  // TAB 4: IR Evaluation Runner
  const executeEvalBtn = document.getElementById("execute-eval-btn");

  executeEvalBtn.addEventListener("click", async () => {
    executeEvalBtn.disabled = true;
    executeEvalBtn.textContent = "Running Benchmark...";
    showToast("Evaluating 6 benchmark queries against ground-truth relevance...");

    try {
      const res = await fetch("/api/evaluation?k=5");
      const data = await res.json();

      document.getElementById("eval-map-val").textContent = data.MAP.toFixed(3);
      document.getElementById("eval-mrr-val").textContent = data.MRR.toFixed(3);
      document.getElementById("eval-p5-val").textContent = (data.mean_precision * 100).toFixed(1) + "%";
      document.getElementById("eval-ndcg-val").textContent = data.mean_ndcg.toFixed(3);

      const tbody = document.getElementById("eval-table-rows");
      tbody.innerHTML = data.queries.map(q => `
        <tr>
          <td><strong>${escapeHtml(q.query)}</strong></td>
          <td><span class="card-caption">${escapeHtml(q.description)}</span></td>
          <td>${q.p_at_k.toFixed(2)}</td>
          <td>${q.r_at_k.toFixed(2)}</td>
          <td>${q.f1_at_k.toFixed(2)}</td>
          <td><span class="meta-pill pill-relevance">${q.ap.toFixed(3)}</span></td>
          <td>${q.ndcg_at_k.toFixed(3)}</td>
          <td>1/${q.rr > 0 ? Math.round(1 / q.rr) : "∞"}</td>
        </tr>
      `).join("");
      showToast("Evaluation suite completed successfully!");
    } catch {
      alert("Error executing evaluation benchmark.");
    } finally {
      executeEvalBtn.disabled = false;
      executeEvalBtn.textContent = "Run Benchmark Suite";
    }
  });

  // TAB 5: Corpus Library Loader
  async function loadCorpusData() {
    const grid = document.getElementById("corpus-cards-grid");
    try {
      const res = await fetch("/api/documents");
      const data = await res.json();
      if (data.documents) {
        grid.innerHTML = data.documents.map(doc => `
          <div class="kpi-box" style="justify-content: space-between;">
            <div>
              <h4 style="font-size:1.05rem; margin-bottom:6px; color:#1e1b4b; font-weight:700;">${escapeHtml(doc.filename)}</h4>
              <span class="kpi-sub">Act Index: #${doc.doc_id}</span>
            </div>
            <div style="margin-top: 16px; display: flex; justify-content: space-between; align-items: center;">
              <span class="meta-pill pill-pr">PageRank: ${doc.pagerank}</span>
              <button class="btn-read-act" onclick="document.dispatchEvent(new CustomEvent('openActFromTable', {detail: ${doc.doc_id}}))">Read Act</button>
            </div>
          </div>
        `).join("");
      }
    } catch {
      grid.innerHTML = `<p class="table-empty-msg" style="color:var(--danger)">Error loading corpus collection.</p>`;
    }
  }
});
