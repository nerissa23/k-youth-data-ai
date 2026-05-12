import sys
from src import ingestor
from pathlib import Path

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR/"data"
SRC_DIR = ROOT_DIR/"src"

def main():
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            match arg:
                case "ingest":
                    print("🥉 Bronze:...")
                    # call ingestor.py
                    ingestor.ingest()
                    # func()
                case "process":
                    print("")
                    # call processor.py
                case "load":
                    print("")
                    # call loader.py
                case "profile":
                    print("")
                    # call profiler
                case _:
                    print("❗ Argument passed is not available")


if __name__ == "__main__":
    main()
