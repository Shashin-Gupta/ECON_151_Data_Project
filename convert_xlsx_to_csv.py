#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert an .xlsx workbook (one sheet) to .csv."
    )
    p.add_argument(
        "input_xlsx",
        nargs="?",
        default="cpsaat39.xlsx",
        help="Path to input .xlsx (default: cpsaat39.xlsx)",
    )
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to output .csv (default: same name as input)",
    )
    p.add_argument(
        "-s",
        "--sheet",
        default=0,
        help="Sheet name or 0-based index (default: 0 / first sheet)",
    )
    p.add_argument(
        "--no-header",
        action="store_true",
        help="Write CSV without a header row",
    )
    p.add_argument(
        "--keep-index",
        action="store_true",
        help="Keep the DataFrame index column in the output CSV",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    in_path = Path(args.input_xlsx).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else in_path.with_suffix(".csv")
    )

    sheet = args.sheet
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)

    df = pd.read_excel(in_path, sheet_name=sheet, engine="openpyxl")
    df.to_csv(
        out_path,
        index=bool(args.keep_index),
        header=not args.no_header,
    )

    print(f"Wrote CSV: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

