"""Command line: ``python -m qplay list`` and ``python -m qplay run <name|all>``."""

from __future__ import annotations

import argparse

from . import __version__, demos


def main(argv=None):
    parser = argparse.ArgumentParser(prog="qplay", description="Physics and maths playground")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list available demos")
    run = sub.add_parser("run", help="render demos to PNG files")
    run.add_argument("names", nargs="+", help="demo names, or 'all'")
    run.add_argument("--out", default="figures", help="output directory (default: figures)")
    args = parser.parse_args(argv)

    if args.command == "list":
        for name in sorted(demos.DEMOS):
            doc = (demos.DEMOS[name].__doc__ or "").strip().splitlines()
            print(f"{name:16s}{doc[0] if doc else ''}")
        return 0

    names = sorted(demos.DEMOS) if args.names == ["all"] else args.names
    for name in names:
        try:
            print(demos.run(name, args.out))
        except KeyError as err:
            parser.error(str(err.args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
