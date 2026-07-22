#!/usr/bin/env python3
"""Validate the curated site database before deployment."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "db.json"


def number(value):
    if value is None or value == "":
        return 0
    return int(value)


def main() -> int:
    data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    votes = data.get("votes", [])
    details = data.get("details", {})
    errors: list[str] = []
    warnings: list[str] = []

    seen: set[tuple[str, str]] = set()
    for vote in votes:
        scrutin = vote.get("Scrutin")
        source = str(vote.get("Source officielle") or "")
        legislature = "?"
        if "/dyn/" in source:
            try:
                legislature = source.split("/dyn/", 1)[1].split("/", 1)[0]
            except IndexError:
                pass

        if scrutin is None:
            # Documentary placeholders are permitted.
            continue

        key = (legislature, str(scrutin))
        if key in seen:
            errors.append(f"Scrutin dupliqué : législature {legislature}, n° {scrutin}")
        seen.add(key)

        rows = details.get(str(scrutin), [])
        if not rows:
            warnings.append(f"Pas de détail par groupe : scrutin n° {scrutin}")
            continue

        sums = {
            "Pour total": sum(number(row.get("Pour")) for row in rows),
            "Contre total": sum(number(row.get("Contre")) for row in rows),
            "Abstention totale": sum(number(row.get("Abstention")) for row in rows),
        }
        for field, actual in sums.items():
            expected = vote.get(field)
            if expected is not None and number(expected) != actual:
                warnings.append(
                    f"Détail partiel ou incohérent, scrutin n° {scrutin}: "
                    f"{field}={expected}, somme groupes={actual}"
                )

        for row in rows:
            effectif = row.get("Effectif")
            participants = row.get("Participants")
            if effectif is not None and participants is not None and number(participants) > number(effectif):
                errors.append(
                    f"Participants supérieurs à l'effectif, scrutin n° {scrutin}, "
                    f"groupe {row.get('Groupe')}"
                )

    print(f"{len(votes)} entrées contrôlées, {len(details)} scrutins avec détail.")
    for warning in warnings[:20]:
        print(f"AVERTISSEMENT: {warning}")
    if len(warnings) > 20:
        print(f"AVERTISSEMENT: {len(warnings) - 20} autre(s) avertissement(s) non affiché(s).")
    for error in errors:
        print(f"ERREUR: {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
