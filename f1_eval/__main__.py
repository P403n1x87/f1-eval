from argparse import ArgumentParser

from f1.listener import PacketListener
from f1_eval.collector import EvalRaceDataCollector


def main():
    argp = ArgumentParser(prog="f1-eval")

    args = argp.parse_args()

    try:
        collector = EvalRaceDataCollector(PacketListener())
        print("Listening for data")
        collector.collect()
    except KeyboardInterrupt:
        print("\nBOX BOX.")


if __name__ == "__main__":
    main()
