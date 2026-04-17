"""CLI entry point for the score command."""
from __future__ import annotations
import argparse
import sys
from envoy.parser import EnvParser, EnvParseError
from envoy.scorer import score, ScoreError


def _load_env_file(path: str) -> dict:
    try:
        with open(path) as fh:
            return EnvParser(fh.read()).parse()
    except (OSError, EnvParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


def run_score(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    env = _load_env_file(args.file)
    try:
        result = score(env)
    except ScoreError as exc:
        print(f"error: {exc}", file=err)
        return 2

    print(result.summary(), file=out)

    if result.has_issues():
        for issue in result.issues:
            print(f"  {issue}", file=out)

    if args.min_score is not None and result.score < args.min_score:
        print(f"error: score {result.score} is below minimum {args.min_score}", file=err)
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="envoy score", description="Score a .env file for quality and security.")
    p.add_argument("file", help="path to .env file")
    p.add_argument("--min-score", type=int, default=None, metavar="N",
                   help="exit 1 if score is below N")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_score(args))


if __name__ == "__main__":
    main()
