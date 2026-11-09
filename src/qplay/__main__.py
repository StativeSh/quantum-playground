"""Command line.

    qplay list                         show demos and animations
    qplay run <name|all> [--out DIR]   render demo figures (PNG)
    qplay animate <name|all> [--frames N] [--fps F] [--out DIR]   render animations (GIF)
"""

from __future__ import annotations

import argparse

from . import __version__, animations, demos


def _summary(fn):
    doc = (fn.__doc__ or "").strip().splitlines()
    return doc[0] if doc else ""


def main(argv=None):
    parser = argparse.ArgumentParser(prog="qplay", description="Physics and maths playground")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list demos and animations")
    run = sub.add_parser("run", help="render demos to PNG files")
    run.add_argument("names", nargs="+", help="demo names, or 'all'")
    run.add_argument("--out", default="figures", help="output directory (default: figures)")
    anim = sub.add_parser("animate", help="render animations to GIF files")
    anim.add_argument("names", nargs="+", help="animation names, or 'all'")
    anim.add_argument("--out", default="figures", help="output directory (default: figures)")
    anim.add_argument("--frames", type=int, default=120, help="number of frames (default: 120)")
    anim.add_argument("--fps", type=int, default=24, help="frames per second (default: 24)")
    args = parser.parse_args(argv)

    if args.command == "list":
        print("Demos (qplay run NAME):")
        for name in sorted(demos.DEMOS):
            print(f"  {name:22s}{_summary(demos.DEMOS[name])}")
        print("Animations (qplay animate NAME):")
        for name in sorted(animations.ANIMATIONS):
            print(f"  {name:22s}{_summary(animations.ANIMATIONS[name])}")
        return 0

    registry = demos.DEMOS if args.command == "run" else animations.ANIMATIONS
    names = sorted(registry) if args.names == ["all"] else args.names
    for name in names:
        try:
            if args.command == "run":
                print(demos.run(name, args.out))
            else:
                print(animations.render(name, args.out, n_frames=args.frames, fps=args.fps))
        except KeyError as err:
            parser.error(str(err.args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
