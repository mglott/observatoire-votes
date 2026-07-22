#!/usr/bin/env python3
"""Detect recent official Assembly scrutins not yet curated in the site.

The script intentionally does not publish them. It creates a review report so a
human can choose the structurally relevant votes and add editorial metadata.
"""
from __future__ import annotations

import io
import json
import re
import urllib.request
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "db.json"
REPORT_JSON = ROOT / "reports" / "new_scrutins.json"
REPORT_MD = ROOT / "reports" / "new_scrutins.md"
OFFICIAL_ZIP = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/loi/"
    "scrutins/Scrutins.json.zip"
)
LOOKBACK_DAYS = 10


def as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def as_text(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.split())
    return ""


def find_first(node: Any, keys: Iterable[str]) -> Any:
    wanted = set(keys)
    if isinstance(node, dict):
        for key, value in node.items():
            if key in wanted and value not in (None, "", [], {}):
                return value
        for value in node.values():
            found = find_first(value, wanted)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_first(value, wanted)
            if found not in (None, "", [], {}):
                return found
    return None


def locate_scrutin(node: Any) -> dict[str, Any] | None:
    if isinstance(node, dict):
        candidate = node.get("scrutin")
        if isinstance(candidate, dict):
            return candidate
        if any(key in node for key in ("dateScrutin", "syntheseVote", "ventilationVotes")):
            return node
        for value in node.values():
            found = locate_scrutin(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = locate_scrutin(value)
            if found:
                return found
    return None


def parse_date(value: Any) -> date | None:
    text = as_text(value)
    if not text:
        return None
    text = text[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_record(payload: Any, filename: str) -> dict[str, Any] | None:
    scrutin = locate_scrutin(payload)
    if not scrutin:
        return None

    number = as_int(scrutin.get("numero"))
    if number is None:
        uid = as_text(scrutin.get("uid")) or filename
        matches = re.findall(r"(\d+)", uid)
        number = as_int(matches[-1]) if matches else None

    scrutiny_date = parse_date(scrutin.get("dateScrutin"))
    if scrutiny_date is None:
        scrutiny_date = parse_date(find_first(scrutin, ("dateScrutin", "date")))

    title = as_text(scrutin.get("titre"))
    if not title:
        title = as_text(find_first(scrutin, ("titre", "libelle")))

    result_node = scrutin.get("sort")
    if isinstance(result_node, dict):
        result = as_text(result_node.get("libelle")) or as_text(result_node.get("code"))
    else:
        result = as_text(result_node)

    if number is None or scrutiny_date is None:
        return None

    return {
        "scrutin": number,
        "date": scrutiny_date.isoformat(),
        "titre_officiel": title or "Titre officiel non extrait",
        "resultat": result,
        "source": f"https://www.assemblee-nationale.fr/dyn/17/scrutins/{number}",
    }


def download_zip() -> bytes:
    request = urllib.request.Request(
        OFFICIAL_ZIP,
        headers={"User-Agent": "ObservatoireVotes/1.0 (+GitHub Actions)"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def main() -> int:
    db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    existing = {
        int(vote["Scrutin"])
        for vote in db.get("votes", [])
        if vote.get("Scrutin") is not None
        and "/dyn/17/" in str(vote.get("Source officielle") or "")
    }

    archive_bytes = download_zip()
    cutoff = date.today() - timedelta(days=LOOKBACK_DAYS)
    candidates: dict[int, dict[str, Any]] = {}

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        for member in archive.namelist():
            if not member.lower().endswith(".json") or member.endswith("/"):
                continue
            try:
                payload = json.loads(archive.read(member).decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            record = parse_record(payload, member)
            if not record:
                continue
            record_date = date.fromisoformat(record["date"])
            if record_date >= cutoff and record["scrutin"] not in existing:
                candidates[record["scrutin"]] = record

    ordered = sorted(candidates.values(), key=lambda row: (row["date"], row["scrutin"]), reverse=True)
    report = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "lookback_days": LOOKBACK_DAYS,
        "count": len(ordered),
        "scrutins": ordered,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scrutins récents à examiner",
        "",
        f"Rapport généré le {report['generated_at']}.",
        f"Fenêtre contrôlée : {LOOKBACK_DAYS} derniers jours.",
        "",
    ]
    if not ordered:
        lines.append("Aucun scrutin récent non répertorié n’a été détecté.")
    else:
        lines.append(
            "Ces scrutins sont détectés automatiquement, mais ne sont **pas publiés** "
            "avant validation de leur intérêt éditorial, de leur thème et de leur titre pédagogique."
        )
        lines.append("")
        for row in ordered:
            lines.extend(
                [
                    f"## Scrutin n° {row['scrutin']} — {row['date']}",
                    "",
                    row["titre_officiel"],
                    "",
                    f"Résultat officiel : {row['resultat'] or 'non extrait'}",
                    "",
                    f"Source : {row['source']}",
                    "",
                ]
            )
    REPORT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"{len(ordered)} scrutin(s) récent(s) à examiner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
