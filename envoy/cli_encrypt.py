"""CLI sub-command: envoy encrypt / decrypt.

Usage examples
--------------
  envoy-encrypt encrypt .env --passphrase s3cr3t --keys DB_PASS,API_KEY -o .env.enc
  envoy-encrypt decrypt .env.enc --passphrase s3cr3t -o .env.dec
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy.encryptor import EncryptionError, decrypt_dict, encrypt_dict
from envoy.parser import EnvParser, EnvParseError
from envoy.exporter import to_dotenv


def _load_env_file(path: str) -> dict[str, str]:
    try:
        return EnvParser(Path(path).read_text()).parse()
    except (OSError, EnvParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _parse_keys(keys_str: Optional[str]) -> Optional[List[str]]:
    if not keys_str:
        return None
    return [k.strip() for k in keys_str.split(",") if k.strip()]


def run_encrypt(
    input_path: str,
    passphrase: str,
    *,
    mode: str = "encrypt",
    keys: Optional[str] = None,
    output: Optional[str] = None,
    stdout=None,
) -> int:
    if stdout is None:  # pragma: no cover
        stdout = sys.stdout

    env = _load_env_file(input_path)
    key_list = _parse_keys(keys)

    try:
        if mode == "encrypt":
            result = encrypt_dict(env, passphrase, keys=key_list)
        else:
            result = decrypt_dict(env, passphrase, keys=key_list)
    except EncryptionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    content = to_dotenv(result)

    if output:
        Path(output).write_text(content)
        print(f"Written to {output}", file=stdout)
    else:
        print(content, file=stdout, end="")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-encrypt",
        description="Encrypt or decrypt secret values inside a .env file.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    for cmd in ("encrypt", "decrypt"):
        p = sub.add_parser(cmd, help=f"{cmd.capitalize()} env values.")
        p.add_argument("input", help="Path to the .env file.")
        p.add_argument("--passphrase", required=True, help="Encryption passphrase.")
        p.add_argument("--keys", default=None, help="Comma-separated keys to process (default: all).")
        p.add_argument("-o", "--output", default=None, help="Output file (default: stdout).")

    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    args = build_parser().parse_args(argv)
    sys.exit(
        run_encrypt(
            args.input,
            args.passphrase,
            mode=args.mode,
            keys=args.keys,
            output=args.output,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
