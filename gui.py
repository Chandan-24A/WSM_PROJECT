import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

class SearchGUI:
    def __init__(self, engine):
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("WSM Search Engine")
        self.root.geometry("900x700")
        self.root.configure(bg="#F4F6F9")

        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass

        self.bg_color = "#F4F6F9"
        self.accent_color = "#2563EB"
        self.text_color = "#1F2937"
        self.card_color = "#FFFFFF"

        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TButton", background=self.accent_color, foreground="white",
                             font=("Segoe UI", 11, "bold"), padding=8, borderwidth=0)
        self.style.map("TButton", background=[("active", "#1D4ED8")])
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color)

        self.title_font = tkfont.Font(family="Segoe UI", size=26, weight="bold")
        self.subtitle_font = tkfont.Font(family="Segoe UI", size=12)
        self.search_font = tkfont.Font(family="Segoe UI", size=14)
        self.result_font = tkfont.Font(family="Segoe UI", size=11)
        self.bold_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")

        header_frame = ttk.Frame(self.root, padding=(20, 40, 20, 30))
        header_frame.pack(fill="x")

        title_label = tk.Label(header_frame, text="Information Retrieval System", font=self.title_font, bg=self.bg_color, fg=self.accent_color)
        title_label.pack()

        subtitle_label = tk.Label(header_frame, text="Intelligent Document Retrieval System", font=self.subtitle_font, bg=self.bg_color, fg="#6B7280")
        subtitle_label.pack(pady=(5, 6))

        help_label = tk.Label(
            header_frame,
            text='Try: king OR crown  |  king AND NOT crown  |  "my lord"  |  king*',
            font=("Segoe UI", 10), bg=self.bg_color, fg="#6B7280"
        )
        help_label.pack(pady=(0, 20))

        search_frame = ttk.Frame(header_frame)
        search_frame.pack(fill="x", padx=100)

        self.entry = tk.Entry(search_frame, font=self.search_font, relief="flat", bd=10,
                              highlightthickness=1, highlightcolor=self.accent_color, highlightbackground="#D1D5DB")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.on_search)

        search_btn = ttk.Button(search_frame, text="Search Documents", command=self.on_search, cursor="hand2")
        search_btn.pack(side="right")

        results_container = ttk.Frame(self.root, padding=(60, 0, 60, 40))
        results_container.pack(fill="both", expand=True)

        # Pagination controls
        self.pagination_frame = ttk.Frame(results_container)
        self.pagination_frame.pack(fill="x", pady=(0, 10))
        self.prev_btn = ttk.Button(self.pagination_frame, text="< Prev", command=self.prev_page)
        self.prev_btn.pack(side="left")
        self.page_label = ttk.Label(self.pagination_frame, text="")
        self.page_label.pack(side="left", padx=20)
        self.next_btn = ttk.Button(self.pagination_frame, text="Next >", command=self.next_page)
        self.next_btn.pack(side="right")
        self.pagination_frame.pack_forget()

        scrollbar = ttk.Scrollbar(results_container)
        scrollbar.pack(side="right", fill="y")

        self.results = tk.Text(results_container, wrap="word", state="disabled",
                               font=self.result_font, bg=self.card_color, fg=self.text_color,
                               relief="flat", highlightthickness=1, highlightbackground="#E5E7EB",
                               yscrollcommand=scrollbar.set, padx=20, pady=20)
        self.results.pack(fill="both", expand=True)
        scrollbar.config(command=self.results.yview)

        self.results.tag_configure("title", font=self.bold_font, foreground=self.accent_color, spacing1=15, spacing3=2)
        self.results.tag_configure("score", foreground="#059669", font=tkfont.Font(family="Segoe UI", size=10, weight="bold"), spacing3=8)
        self.results.tag_configure("preview", foreground="#4B5563", spacing3=20)
        self.results.tag_configure("error", foreground="#DC2626", font=self.search_font, spacing1=20, justify="center")
        self.results.tag_configure("meta", foreground="#6B7280", font=tkfont.Font(family="Segoe UI", size=10, slant="italic"), spacing3=15)
        self.results.tag_configure("highlight", background="#FEF08A", foreground="#000000")
        self.results.tag_configure("dym", foreground="#2563EB", font=tkfont.Font(family="Segoe UI", size=12, underline=1), spacing1=10)
        self.results.tag_bind("dym", "<Button-1>", self.apply_suggestion)
        self.results.tag_bind("dym", "<Enter>", lambda event: self.results.config(cursor="hand2"))
        self.results.tag_bind("dym", "<Leave>", lambda event: self.results.config(cursor=""))

        self.current_results = []
        self.current_matched_terms = []
        self.page = 0
        self.results_per_page = 5
        self.query = ""
        self.dym = None

    def show_message(self, message, tag="error"):
        self.results.config(state="normal")
        self.results.delete("1.0", "end")
        self.results.insert("end", message + "\n", tag)
        self.results.config(state="disabled")
        self.pagination_frame.pack_forget()

    def on_search(self, event=None):
        query = self.entry.get()
        response = self.engine.search(query)
        status = response["status"]

        dym = response.get("did_you_mean")

        if status == "empty":
            self.show_message("Please enter a search query above.", "error")
            return
        if status == "query_error":
            self.show_message(f"Invalid query: {response['message']}.", "error")
            return
        if status == "only_stopwords":
            self.show_message("Your query contains only common words (stop words).\nTry using more specific terms.", "error")
            return
        if status == "no_match":
            msg = f"No matching documents found for '{query}'."
            self.show_message(msg, "error")
            if dym:
                self.results.config(state="normal")
                self.results.insert("end", f"\nDid you mean: {dym}\n", "dym")
                self.results.config(state="disabled")
            return

        self.current_results = response["results"]
        self.current_matched_terms = response["matched_terms"]
        self.page = 0
        self.query = query
        self.dym = dym
        self.render_page()

    def apply_suggestion(self, event=None):
        if self.dym:
            self.entry.delete(0, "end")
            self.entry.insert(0, self.dym)
            self.on_search()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.render_page()

    def next_page(self):
        if (self.page + 1) * self.results_per_page < len(self.current_results):
            self.page += 1
            self.render_page()

    def render_page(self):
        self.pagination_frame.pack(fill="x", pady=(0, 10), before=self.results)
        self.results.config(state="normal")
        self.results.delete("1.0", "end")

        num_results = len(self.current_results)
        self.results.insert("end", f"Found {num_results} result(s) for '{self.query}'\n", "meta")
        if self.dym:
            self.results.insert("end", f"Did you mean: {self.dym}\n", "dym")

        start_idx = self.page * self.results_per_page
        end_idx = min(start_idx + self.results_per_page, num_results)
        page_results = self.current_results[start_idx:end_idx]

        total_pages = (num_results + self.results_per_page - 1) // self.results_per_page
        self.page_label.config(text=f"Page {self.page + 1} of {total_pages}")

        if self.page > 0:
            self.prev_btn.state(["!disabled"])
        else:
            self.prev_btn.state(["disabled"])

        if end_idx < num_results:
            self.next_btn.state(["!disabled"])
        else:
            self.next_btn.state(["disabled"])

        for i, result in enumerate(page_results, start=start_idx + 1):
            title = f"{i}. {result['filename']}\n"
            score_text = f"Relevance: {result['relative']:.0f}%  |  Score: {result['score']:.4f}\n"
            preview = f"\"{result['preview']}\"\n"

            self.results.insert("end", title, "title")
            self.results.insert("end", score_text, "score")

            start_pos = self.results.index("end-1c")
            self.results.insert("end", preview, "preview")

            for term in self.current_matched_terms:
                if len(term) < 2: continue
                idx = start_pos
                while True:
                    idx = self.results.search(term, idx, nocase=1, stopindex="end")
                    if not idx:
                        break
                    lastidx = f"{idx}+{len(term)}c"
                    self.results.tag_add("highlight", idx, lastidx)
                    idx = lastidx

        self.results.config(state="disabled")

    def run(self):
        self.root.mainloop()
