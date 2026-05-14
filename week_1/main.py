import sys
from src import ingestor, processor, loader
from pathlib import Path

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
                    print("🥈 Silver:...")
                    # call processor.py
                    processor.process()
                case "load":
                    print("🥇 Gold:...")
                    # call loader.py
                    loader.load()
                case "profile":
                    print("")
                    # call profiler
                case _:
                    print("❗ Argument passed is not available")


if __name__ == "__main__":
    main()
