"""Read a case folder, check it, and hand back its contents.

A case folder holds case.json plus the files it links to. Each file is checked
against its schema in catalog/schemas/, then the files are checked against
each other (a puzzle that unlocks a location must name a sealed location, the
killer must be a core role, and so on). Every problem found is reported at
once, so a case author can fix them in one pass.
"""

import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from django.conf import settings
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
FILE_KINDS = ("roles", "clues", "puzzles", "props", "solution", "extras")
REQUIRED_KINDS = ("roles", "clues", "puzzles", "props", "solution")


class CaseError(Exception):
    def __init__(self, folder, problems):
        self.folder = folder
        self.problems = problems
        super().__init__(f"{folder}: " + "; ".join(problems))


@dataclass
class CaseBundle:
    folder: Path
    manifest: dict
    roles: list
    clues: dict
    puzzles: list
    props: list
    solution: dict
    extras: dict = field(default_factory=dict)

    @property
    def slug(self):
        return self.manifest["slug"]

    def role(self, role_id):
        return next((r for r in self.roles if r["id"] == role_id), None)

    @property
    def clue_count(self):
        return len(self.clues.get("body", [])) + len(self.clues.get("cards", []))

    @property
    def map_url(self):
        """Where browsers load the map from, or "" if the case has none."""
        ref = self.manifest.get("map", "")
        if not ref or ref.startswith("https://"):
            return ref
        return f"/cases/{self.slug}/{ref}"


@cache
def _validator(kind):
    schema = json.loads((SCHEMA_DIR / f"{kind}.schema.json").read_text())
    return Draft202012Validator(schema)


def _schema_problems(kind, data, filename):
    problems = []
    for err in sorted(_validator(kind).iter_errors(data), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in err.absolute_path) or "(top level)"
        problems.append(f"{filename} {where}: {err.message}")
    return problems


def _read_json(path, problems):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"{path.name}: file not found")
    except json.JSONDecodeError as e:
        problems.append(f"{path.name}: not valid JSON (line {e.lineno}, column {e.colno}: {e.msg})")
    return None


def _inside(folder, relative):
    """The path of `relative` inside `folder`, or None if it points outside."""
    path = (folder / relative).resolve()
    return path if path.is_relative_to(folder.resolve()) else None


def load_case(folder):
    """Load and check one case folder. Raises CaseError listing every problem."""
    folder = Path(folder)
    problems = []

    manifest = _read_json(folder / "case.json", problems)
    if manifest is None:
        raise CaseError(folder, problems)
    problems += _schema_problems("case", manifest, "case.json")
    if problems:
        raise CaseError(folder, problems)

    data = {}
    for kind in FILE_KINDS:
        name = manifest["files"].get(kind)
        if name is None:
            data[kind] = {}
            continue
        path = _inside(folder, name)
        if path is None:
            problems.append(f"case.json files/{kind}: {name} is outside the case folder")
            continue
        content = _read_json(path, problems)
        if content is not None:
            problems += _schema_problems(kind, content, name)
            data[kind] = content
    if problems:
        raise CaseError(folder, problems)

    bundle = CaseBundle(folder=folder, manifest=manifest, **data)
    problems += _cross_check(bundle)
    if problems:
        raise CaseError(folder, problems)
    return bundle


def _duplicates(ids):
    seen, dupes = set(), set()
    for i in ids:
        (dupes if i in seen else seen).add(i)
    return sorted(dupes)


def _cross_check(b):
    problems = []
    m = b.manifest
    if b.folder.name != m["slug"]:
        problems.append(f"case.json slug: {m['slug']!r} does not match the folder name {b.folder.name!r}")

    role_ids = [r["id"] for r in b.roles]
    for d in _duplicates(role_ids):
        problems.append(f"roles: id {d!r} is used more than once")
    core = [r["id"] for r in b.roles if r["core"]]
    optional = {r["id"] for r in b.roles if not r["core"]}

    if m["min_players"] > m["max_players"]:
        problems.append("case.json: min_players is more than max_players")
    if m["min_players"] < len(core):
        problems.append(f"case.json min_players: {m['min_players']} is fewer than the {len(core)} core roles")
    if m["max_players"] > len(b.roles):
        problems.append(f"case.json max_players: {m['max_players']} is more than the {len(b.roles)} roles")

    if b.solution["killer"] not in role_ids:
        problems.append(f"solution killer: {b.solution['killer']!r} is not a role id")
    elif b.solution["killer"] not in core:
        problems.append(f"solution killer: {b.solution['killer']!r} must be a core role so it is always cast")

    rounds = b.clues["rounds"]
    clue_ids = [c["id"] for c in b.clues.get("body", []) + b.clues.get("cards", [])]
    for d in _duplicates(clue_ids):
        problems.append(f"clues: id {d!r} is used more than once")
    for kind in ("body", "cards"):
        for c in b.clues.get(kind, []):
            if c["round"] > rounds:
                problems.append(f"clues {kind} {c['id']}: round {c['round']} is past the last round ({rounds})")
            if "requires_role" in c and c["requires_role"] not in optional:
                problems.append(f"clues cards {c['id']}: requires_role {c['requires_role']!r} is not an optional role")
            if "shows" in c and c["shows"] not in b.extras:
                problems.append(f"clues cards {c['id']}: shows {c['shows']!r}, which extras.json does not have")

    puzzle_ids = [p["id"] for p in b.puzzles]
    for d in _duplicates(puzzle_ids):
        problems.append(f"puzzles: id {d!r} is used more than once")
    sealed = {s["location"] for s in b.clues.get("sealed", [])}
    for s in b.clues.get("sealed", []):
        if s.get("unlocked_by_puzzle") and s["unlocked_by_puzzle"] not in puzzle_ids:
            problems.append(f"clues sealed {s['location']!r}: unlocked_by_puzzle {s['unlocked_by_puzzle']!r} is not a puzzle id")
        if s.get("unlocked_by_round", 1) > rounds:
            problems.append(f"clues sealed {s['location']!r}: unlocked_by_round is past the last round ({rounds})")

    room_ids = {r["id"] for r in b.extras.get("map", {}).get("rooms", [])}
    for p in b.puzzles:
        if "unlocks" in p and p["unlocks"] not in sealed:
            problems.append(f"puzzles {p['id']}: unlocks {p['unlocks']!r}, which is not a sealed location in clues.json")
        if "shows" in p and p["shows"] not in b.extras:
            problems.append(f"puzzles {p['id']}: shows {p['shows']!r}, which extras.json does not have")
        if p["answer"]["type"] == "route":
            for room in [p["answer"]["start"], *p["answer"]["sequence"]]:
                if room not in room_ids:
                    problems.append(f"puzzles {p['id']}: route room {room!r} is not a room in extras.json map")

    prop_ids = [p["id"] for p in b.props]
    for d in _duplicates(prop_ids):
        problems.append(f"props: id {d!r} is used more than once")
    for p in b.props:
        if "clue" in p and p["clue"] not in clue_ids:
            problems.append(f"props {p['id']}: clue {p['clue']!r} is not a clue id")
    for r in b.roles:
        for prop in r.get("starting_props", []):
            if prop not in prop_ids:
                problems.append(f"roles {r['id']}: starting prop {prop!r} is not in props.json")

    map_ref = m.get("map", "")
    if map_ref and not map_ref.startswith("https://"):
        path = _inside(b.folder / "public", map_ref.removeprefix("public/"))
        if not map_ref.startswith("public/") or path is None:
            problems.append(f"case.json map: {map_ref!r} must be an https:// link or a file under public/")
        elif not path.is_file():
            problems.append(f"case.json map: {map_ref} not found")
    return problems


def case_folders(cases_dir=None):
    """Every folder in CASES_DIR that has a case.json."""
    cases_dir = Path(cases_dir or settings.CASES_DIR)
    return sorted(p.parent for p in cases_dir.glob("*/case.json"))


_bundle_cache = {}


def bundle_for(case):
    """The checked contents of a Case row's folder, cached until it is re-imported."""
    cached = _bundle_cache.get(case.pk)
    if cached is None or cached[0] != case.imported_at:
        cached = (case.imported_at, load_case(Path(settings.CASES_DIR) / case.folder))
        _bundle_cache[case.pk] = cached
    return cached[1]
