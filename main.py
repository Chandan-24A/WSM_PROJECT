import os

from src.search_engine import SearchEngine
from gui import SearchGUI

DOCUMENTS_DIR = "data_files"


def main():
    engine = SearchEngine(DOCUMENTS_DIR)
    engine.build_index()
    print("Index built. Documents:", engine.index.document_count(),
          "Vocabulary size:", len(engine.index.vocabulary()))

    gui = SearchGUI(engine)
    gui.run()


if __name__ == "__main__":
    main()
