"""
stignore-agent helpers

Various helper functions to remove complexity from app views
"""
from types import SimpleNamespace
from pathlib import Path


def parse_config(config):
    """
    Takes a basic config object and returns the transformed one the app requires
    """
    return {
        "base_folder": Path(config["base_folder"]),
        "folders": {
            folder["name"]: SimpleNamespace(
                path=Path(config["base_folder"]) / folder["name"],
                depth=folder.get("depth", 0),
            )
            for folder in config["folders"]
        },
    }


def load_stignore_file(filename, sort=True):
    """
    Loads a provided stignore filename
    Parses it into a list of entry objects and returns them
    """
    entries = []

    with open(filename, "rt", encoding="utf-8") as stignore_file:
        for line in stignore_file:
            if line.endswith("\n"):
                line = line[:-1]

            if line.startswith("!"):
                ignore_type = "keep"
                name = line[1:]
            else:
                ignore_type = "ignore"
                name = line

            # We want to drop the trailing slash
            # As this means 'the contents of the folder but not the folder itself
            # And we want the folder itself included in this decision
            if name.endswith("/"):
                name = name[:-1]

            entries.append(
                {
                    "raw": line,
                    "name": name,
                    "ignore_type": ignore_type,
                }
            )

    if sort:
        entries = sorted(entries, key=lambda x: x["raw"])

    return entries


def stignore_actions(entries, content_folder, include_size=True):
    """
    Takes a list of stignore entities
    Returns a list of actions to align the entities to what appears on disk
    """
    actions = []

    for entry in entries:
        if entry["ignore_type"] != "ignore":
            # We're only looking for entries that could result in cleaning up
            continue

        entry_path = content_folder / entry["name"]

        if not entry_path.exists():
            # Only looking for entry_path's that exist
            continue

        action = {
            "name": str(entry_path.name),
            "path": str(entry_path),
            "action": "delete",
        }

        if include_size:
            size_bytes = sum(
                f.stat().st_size for f in entry_path.glob("**/*") if f.is_file()
            )
            action["size_megabytes"] = size_bytes / 1024 / 1024

        actions.append(action)

    return actions


def load_actions(actions):
    """
    Parses a list of provided entity actions
    Returns a list of raw entity lines to add, and another to remove
    """
    parsed = {
        "ok": True,
        "add": [],
        "remove": [],
    }

    for action in actions:
        if action.get("action") not in ("add", "remove"):
            return {"ok": False, "msg": "Payload action is invalid"}

        if action.get("ignore_type") not in ("keep", "ignore"):
            return {"ok": False, "msg": "Payload ignore_type is invalid"}

        if action.get("ignore_type") == "keep":
            new_entry = f"!{action['name']}"
        else:
            new_entry = action["name"]

        if not new_entry.endswith("/"):
            new_entry = f"{new_entry}/"

        if action.get("action") == "add":
            parsed["add"].append(new_entry)
        elif action.get("action") == "remove":
            parsed["remove"].append(new_entry)
        else:
            return {"ok": False, "msg": "Payload action is invalid"}

    return parsed
