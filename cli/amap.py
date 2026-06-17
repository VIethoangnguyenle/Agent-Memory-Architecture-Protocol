#!/usr/bin/env python3
"""AMAP CLI — Agent Memory Architecture Protocol.

Usage:
    amap init [--target DIR] [--source DIR]
    amap status [--target DIR]
    amap --version
    amap --help

Commands:
    init      Scaffold AMAP framework into a target project
    status    Show current AMAP configuration in a project
"""

import argparse
import sys
import os


def _ensure_importable():
    """When run as `python cli/amap.py`, ensure repo root is on sys.path."""
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(cli_dir)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def main():
    from cli import __version__

    parser = argparse.ArgumentParser(
        prog="amap",
        description="AMAP — Agent Memory Architecture Protocol CLI",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ─── init ───
    init_parser = subparsers.add_parser(
        "init",
        help="Scaffold AMAP framework into a target project",
    )
    init_parser.add_argument(
        "--target",
        default=".",
        help="Target directory to scaffold into (default: current directory)",
    )
    init_parser.add_argument(
        "--source",
        default=None,
        help="AMAP repo root (default: auto-detect from CLI location)",
    )

    # ─── status ───
    status_parser = subparsers.add_parser(
        "status",
        help="Show current AMAP configuration in a project",
    )
    status_parser.add_argument(
        "--target",
        default=".",
        help="Project directory to check (default: current directory)",
    )

    args = parser.parse_args()

    if args.command == "init":
        from cli.commands.init import run_init
        run_init(target_dir=args.target, amap_root=args.source)
    elif args.command == "status":
        from cli.commands.status import run_status
        run_status(target_dir=args.target)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _ensure_importable()
    main()
