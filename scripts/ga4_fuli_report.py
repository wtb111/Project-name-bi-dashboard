#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List
from urllib.request import Request, urlopen
from urllib.error import HTTPError

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GoogleRequest
except Exception:
    service_account = None
    GoogleRequest = None

GA4_SCOPE = ["https://www.googleapis.com/auth/analytics.readonly"]
GA4_RUN_REPORT_URL = "https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"


def iso_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")


def today_utc() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def days_ago_utc(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


def load_service_account_credentials(path: str):
    if service_account is None or GoogleRequest is None:
        raise RuntimeError(
            "Missing google-auth dependency. Install with: pip install google-auth"
        )
    creds = service_account.Credentials.from_service_account_file(path, scopes=GA4_SCOPE)
    creds.refresh(GoogleRequest())
    return creds


def run_report(access_token: str, property_id: str, body: Dict) -> Dict:
    url = GA4_RUN_REPORT_URL.format(property_id=property_id)
    req = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"GA4 API request failed: {e.code} {detail}") from e


def parse_daily_rows(resp: Dict) -> List[Dict]:
    rows = []
    for row in resp.get("rows", []):
        dims = row.get("dimensionValues", [])
        mets = row.get("metricValues", [])
        date_raw = dims[0].get("value", "") if dims else ""
        date_fmt = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(date_raw) == 8 else date_raw
        rows.append(
            {
                "date": date_fmt,
                "activeUsers": float(mets[0].get("value", 0)) if len(mets) > 0 else 0,
                "newUsers": float(mets[1].get("value", 0)) if len(mets) > 1 else 0,
            }
        )
    return rows


def parse_retention_rows(resp: Dict) -> List[Dict]:
    rows = []
    for row in resp.get("rows", []):
        dims = row.get("dimensionValues", [])
        mets = row.get("metricValues", [])
        date_raw = dims[0].get("value", "") if len(dims) > 0 else ""
        first_raw = dims[1].get("value", "") if len(dims) > 1 else ""
        date_fmt = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(date_raw) == 8 else date_raw
        first_fmt = f"{first_raw[:4]}-{first_raw[4:6]}-{first_raw[6:8]}" if len(first_raw) == 8 else first_raw
        rows.append(
            {
                "date": date_fmt,
                "firstSessionDate": first_fmt,
                "activeUsers": float(mets[0].get("value", 0)) if len(mets) > 0 else 0,
            }
        )
    return rows


def build_retention_lookup(raw_rows: List[Dict], mode: str, retention_rows: List[Dict] | None = None) -> Dict[str, Dict[str, int]]:
    """
    mode=zero:
      次留/3留/7留 全部置 0

    mode=proxy-new-users:
      使用未来第 N 天 newUsers 作为近似占位值，仅用于前端联调，
      不代表真实 GA4 cohort 留存口径。

    mode=cohort-active-users:
      使用 GA4 查询(date, firstSessionDate, activeUsers) 计算留存人数：
      - 次留: date - firstSessionDate = 1
      - 3留: date - firstSessionDate = 3
      - 7留: date - firstSessionDate = 7
    """
    lookup: Dict[str, Dict[str, int]] = {}
    by_date = {row["date"]: row for row in raw_rows}
    parsed_dates = sorted(by_date.keys())

    for d in parsed_dates:
        lookup[d] = {"次留": 0, "3留": 0, "7留": 0}

    if mode == "proxy-new-users":
        for d in parsed_dates:
            base_date = datetime.strptime(d, "%Y-%m-%d")
            for days, label in [(1, "次留"), (3, "3留"), (7, "7留")]:
                future = (base_date + timedelta(days=days)).strftime("%Y-%m-%d")
                future_row = by_date.get(future)
                if future_row:
                    lookup[d][label] = int(round(future_row.get("newUsers", 0)))
        return lookup

    if mode == "cohort-active-users" and retention_rows:
        for row in retention_rows:
            first_date = row.get("firstSessionDate")
            active_date = row.get("date")
            if not first_date or not active_date:
                continue
            try:
                diff = (datetime.strptime(active_date, "%Y-%m-%d") - datetime.strptime(first_date, "%Y-%m-%d")).days
            except ValueError:
                continue
            label = {1: "次留", 3: "3留", 7: "7留"}.get(diff)
            if not label:
                continue
            if first_date not in lookup:
                lookup[first_date] = {"次留": 0, "3留": 0, "7留": 0}
            lookup[first_date][label] += int(round(row.get("activeUsers", 0)))
        return lookup

    return lookup


def build_output_rows(raw_rows: List[Dict], retention_mode: str = "zero", retention_rows: List[Dict] | None = None) -> List[Dict]:
    updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    retention_lookup = build_retention_lookup(raw_rows, retention_mode, retention_rows=retention_rows)
    output = []
    for row in raw_rows:
        active = int(round(row.get("activeUsers", 0)))
        new_users = int(round(row.get("newUsers", 0)))
        old_active = max(active - new_users, 0)
        retention = retention_lookup.get(row["date"], {"次留": 0, "3留": 0, "7留": 0})
        output.append(
            {
                "日期": row["date"],
                "总活跃": active,
                "老用户日活": old_active,
                "新增": new_users,
                "次留": retention["次留"],
                "3留": retention["3留"],
                "7留": retention["7留"],
                "操作时间": updated_at,
            }
        )
    output.sort(key=lambda x: x["日期"], reverse=True)
    return output


def main():
    parser = argparse.ArgumentParser(description="Fetch 51福利导航 daily GA4 metrics into dashboard JSON format")
    parser.add_argument("--property-id", required=True, help="GA4 property id")
    parser.add_argument("--service-account-json", default=os.getenv("GA4_SERVICE_ACCOUNT_JSON", ""), help="Path to service account json")
    parser.add_argument("--start-date", default=days_ago_utc(30), help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=today_utc(), help="YYYY-MM-DD")
    parser.add_argument("--output", default="", help="Write JSON to file instead of stdout")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--raw", action="store_true", help="Output raw GA4 rows instead of dashboard format")
    parser.add_argument(
        "--retention-mode",
        default="zero",
        choices=["zero", "proxy-new-users", "cohort-active-users"],
        help="Retention fill strategy: zero = fill 0; proxy-new-users = temporary placeholder; cohort-active-users = use GA4 date + firstSessionDate + activeUsers to compute retention counts",
    )
    args = parser.parse_args()

    if not args.service_account_json:
        print("Missing --service-account-json or GA4_SERVICE_ACCOUNT_JSON", file=sys.stderr)
        sys.exit(2)

    start_date = iso_date(args.start_date)
    end_date = iso_date(args.end_date)

    creds = load_service_account_credentials(args.service_account_json)
    daily_body = {
        "dimensions": [{"name": "date"}],
        "metrics": [{"name": "activeUsers"}, {"name": "newUsers"}],
        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
        "limit": 100000,
        "orderBys": [{"dimension": {"dimensionName": "date"}, "desc": False}],
    }

    retention_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=31)).strftime("%Y-%m-%d")
    retention_body = {
        "dimensions": [{"name": "date"}, {"name": "firstSessionDate"}],
        "metrics": [{"name": "activeUsers"}],
        "dateRanges": [{"startDate": retention_start_date, "endDate": end_date}],
        "limit": 100000,
        "orderBys": [
            {"dimension": {"dimensionName": "date"}, "desc": False},
            {"dimension": {"dimensionName": "firstSessionDate"}, "desc": False}
        ],
    }

    daily_resp = run_report(creds.token, args.property_id, daily_body)
    raw_rows = parse_daily_rows(daily_resp)

    retention_rows = []
    if args.retention_mode == "cohort-active-users":
        retention_resp = run_report(creds.token, args.property_id, retention_body)
        retention_rows = parse_retention_rows(retention_resp)

    payload = raw_rows if args.raw else build_output_rows(raw_rows, retention_mode=args.retention_mode, retention_rows=retention_rows)

    data = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(data)
    else:
        print(data)


if __name__ == "__main__":
    main()
