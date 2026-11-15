"""Turning a list of player names into a cast of roles."""

import random


class CastingError(Exception):
    def __init__(self, problems):
        self.problems = problems
        super().__init__("; ".join(problems))


def cast_roles(roles, min_players, max_players, rows, rng=random):
    """Give every row a role.

    `rows` is a list of (name, role_id) pairs, where role_id is "" to let the
    app choose. Chosen roles are kept; the rest are filled with the remaining
    core roles first, then optional roles, both in random order. Returns a
    list of (name, role_id) in the same order as `rows`.
    """
    problems = []
    names = [name.strip() for name, _ in rows]
    by_id = {r["id"]: r for r in roles}

    if not min_players <= len(rows) <= max_players:
        problems.append(f"This case needs {min_players} to {max_players} players; you have {len(rows)}.")
    if any(not n for n in names):
        problems.append("Every player needs a name.")
    lowered = [n.lower() for n in names if n]
    if len(set(lowered)) != len(lowered):
        problems.append("Two players have the same name; add an initial so you can tell them apart.")

    chosen = [role_id for _, role_id in rows if role_id]
    for role_id in chosen:
        if role_id not in by_id:
            problems.append(f"{role_id!r} is not a role in this case.")
    if len(set(chosen)) != len(chosen):
        problems.append("The same character is picked for two players.")
    if problems:
        raise CastingError(problems)

    free_core = [r["id"] for r in roles if r["core"] and r["id"] not in chosen]
    free_optional = [r["id"] for r in roles if not r["core"] and r["id"] not in chosen]
    open_slots = len(rows) - len(chosen)
    if len(free_core) > open_slots:
        missing = ", ".join(by_id[i]["name"] for i in free_core)
        raise CastingError([f"Every core character must be played. Still uncast: {missing}."])

    rng.shuffle(free_core)
    rng.shuffle(free_optional)
    pool = iter(free_core + free_optional)
    return [(name, role_id or next(pool)) for name, (_, role_id) in zip(names, rows)]
