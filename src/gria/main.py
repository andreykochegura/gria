# TODO

import sys
from gria import parser
from gria import analyzer


def main():
    path = sys.argv[1]
    data = parser.parse(path)
    analyzer.analyze(data)


if __name__ == "__main__":
    main()
