"""
stignore-agent

A basic flask API that provides a set of endpoints to:
* Work with content types (folders underneath the base)
* Manipulate each content types .stignore file
"""
from pathlib import Path

from flask import Flask, current_app, request, jsonify


app = Flask(__name__)


@app.route("/api/v1/types")
def list_content_types():
    """Returns all configured content type folders"""
    folders = current_app.config["folders"]

    return jsonify(
        {
            "ok": True,
            "content_types": [i["name"] for i in folders],
        }
    )


@app.route("/api/v1/<str:content_type>/listing")
def content_type_listing(content_type: str):
    """
    Given a valid content type we return a listing of all folders underneath it
    Also respecting configured search depth
    """
    base_folder = Path(current_app.config["base_folder"])

    for content_folder in current_app.config["folders"]:
        if content_type == content_folder["name"]:
            break
    else:
        return jsonify({"ok": False, "msg": "Provided content_type is not monitored"})

    # pylint: disable=undefined-loop-variable
    search_depth = content_folder.get("depth", 0) + 1
    # pylint: enable=undefined-loop-variable

    content_folder = base_folder / content_type

    if not content_folder.exists():
        return jsonify({"ok": False, "msg": "Provided content_type does not exist"})

    folders = []

    search_glob = "/".join("*" * search_depth)

    for content in content_folder.glob(search_glob):
        if not content.is_dir():
            # We're only interested in folders
            continue

        folders.append(
            {
                "name": content.name,
                "size_bytes": sum(
                    f.stat().st_size for f in content.glob("**/*") if f.is_file()
                ),
            }
        )

    return jsonify(
        {
            "ok": True,
            "folders": folders,
            "count": len(folders),
        }
    )


@app.route("/api/v1/<str:content_type>/stignore")
def stignore_listing(content_type: str):
    """
    Given a valid content type we return the .stignore files contents
    """
    base_folder = Path(current_app.config["base_folder"])

    for content_folder in current_app.config["folders"]:
        if content_type == content_folder["name"]:
            break
    else:
        return jsonify({"ok": False, "msg": "Provided content_type is not monitored"})

    content_folder = base_folder / content_type

    stignore = content_folder / ".stignore"

    if not stignore.exists():
        return jsonify(
            {
                "ok": False,
                "msg": ".stignore doesn't exists for the provided content_type",
            }
        )

    entries = []

    with open(stignore, "rt", encoding="utf-8") as stignore_file:
        for line in stignore_file:
            if line.startswith("!"):
                ignore_type = "keep"
                name = line[1:]
            else:
                ignore_type = "ignore"
                name = line

            if name.endswith("/"):
                name = line[:-1]

            entries.append(
                {
                    "entry": line,
                    "name": name,
                    "type": ignore_type,
                }
            )

    return jsonify(
        {
            "ok": True,
            "entries": entries,
            "count": len(entries),
        }
    )


@app.route("/api/v1/<str:content_type>/stignore", methods=["POST"])
def stignore_modification(content_type: str):
    """
    Apply a modification to the stignore file
    We do not perform any 'cleanup' associated with the modification
    Calling the flush endpoint will trigger that
    """
    base_folder = Path(current_app.config["base_folder"])

    for content_folder in current_app.config["folders"]:
        if content_type == content_folder["name"]:
            break
    else:
        return jsonify({"ok": False, "msg": "Provided content_type is not monitored"})

    content_folder = base_folder / content_type

    stignore = content_folder / ".stignore"

    if not stignore.exists():
        return jsonify(
            {
                "ok": False,
                "msg": ".stignore doesn't exists for the provided content_type",
            }
        )

    entries = []

    with open(stignore, "rt", encoding="utf-8") as stignore_file:
        for line in stignore_file:
            entries.append(line)

    # Insert the payload
    payload = request.get_json(force=True)

    actions = {
        "add": [],
        "remove": [],
    }

    for action in payload["actions"]:
        if action["action"] not in ("add", "remove"):
            return jsonify({"ok": False, "msg": "Payload action is invalid"})

        if action["type"] not in ("keep", "ignore"):
            return jsonify({"ok": False, "msg": "Payload type is invalid"})

        if action["type"] == "keep":
            new_entry = f"!{action['name']}"
        else:
            new_entry = action["name"]

        if not new_entry.endswith("/"):
            new_entry = f"{new_entry}/"

        if action["action"] == "add":
            actions["add"].append(new_entry)
        elif action["action"] == "remove":
            actions["remove"].append(new_entry)

    for entry in actions["remove"]:
        if entry in entries:
            entries.remove(entry)

    for entry in actions["add"]:
        if entry not in entries:
            entries.append(entry)

    # Write out new stignore file
    entries.sort()

    with open(stignore, "wt", encoding="utf-8") as stignore_file:
        stignore_file.writelines(entries)

    return jsonify({"ok": True, "msg": "Actions applied"})


@app.route("/api/v1/<str:content_type>/stignore/flush")
def stignore_flush(content_type: str):
    """
    Prepare a list of actions that would occur if a flush was to happen
    This is a fail safe for the user to verify what *would* happen
    """
    return jsonify(content_type)


@app.route("/api/v1/<str:content_type>/stignore/flush", methods=["POST"])
def stignore_flush(content_type: str):
    """
    Flush the stignore file by performing all operations marked in it
    This is mainly used to clean up all folders we've marked to ignore
    """
    payload = request.get_json(force=True)
    payload["content_type"] = content_type

    return jsonify(payload)
