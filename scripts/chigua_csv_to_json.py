#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Convert 51吃瓜 CSV to dashboard JSON passthrough')
    parser.add_argument('--input', required=True, help='Path to chigua CSV')
    parser.add_argument('--output', required=True, help='Output JSON path')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f'input not found: {input_path}')

    with input_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row = {str(k).strip(): ('' if v is None else str(v).strip()) for k, v in row.items()}
            if row.get('日期'):
                rows.append(row)

    rows.sort(key=lambda r: r.get('日期', ''), reverse=True)

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding='utf-8'
    )


if __name__ == '__main__':
    main()
