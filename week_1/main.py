import sys
from src import ingestor, processor, loader, profiler
from pathlib import Path

def main():
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            match arg:
                case "ingest":
                    ingestor.ingest()
                case "process":
                    processor.process()
                case "load":
                    loader.load()
                case "profile":
                    profiler.profile()
                case "all":
                    ingestor.ingest()
                    processor.process()
                    loader.load()
                    profiler.profile()
                case _:
                    print("Usage: python main.py [ingest|process|load|profile|all]")
    else:
        print("Usage: python main.py [ingest|process|load|profile|all]")

if __name__ == "__main__":
    main()
