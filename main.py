import os
import sys

# Ensure project root is in sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from src.search_engine import SearchEngine

DOCUMENTS_DIR = os.path.join(PROJECT_DIR, "data_files")


def run_web(port=5000):
    from app import app
    print("=" * 64)
    print(" Information Retrieval System - Web Search & Mining")
    print("=" * 64)
    print(f" Server running at: http://127.0.0.1:{port}")
    print(" Press Ctrl+C in this terminal to terminate the server.")
    print("=" * 64)
    app.run(host="0.0.0.0", port=port, debug=False)


def run_gui():
    from gui import SearchGUI
    engine = SearchEngine(DOCUMENTS_DIR)
    engine.build_index()
    print("Index built. Documents:", engine.index.document_count(),
          "Vocabulary size:", len(engine.index.vocabulary()))
    gui = SearchGUI(engine)
    gui.run()


def main():
    if "--gui" in sys.argv:
        run_gui()
    else:
        port = int(os.environ.get("PORT", 5000))
        run_web(port=port)


if __name__ == "__main__":
    main()
