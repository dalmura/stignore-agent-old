"""
stignore-agent

A basic flask API that provides a set of endpoints to:
* Work with content types (folders underneath the base)
* Manipulate each content types .stignore file
"""
import shutil

from flask import Flask, current_app, request, jsonify, send_from_directory

from stignore_agent.helpers import load_stignore_file, stignore_actions, load_actions


app = Flask("stignore-agent")


@app.after_request
def after_request(response):
    """Apply extra CORS header"""
    headers = response.headers
    headers["Access-Control-Allow-Origin"] = "*"
    headers["Access-Control-Allow-Methods"] = "*"
    headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.route("/")
def info_page():
    """Basic info page for users discovering this through their browser"""
    return jsonify(
        {
            "ok": True,
            "msg": "Please visit https://github.com/dalmura/stignore-agent for more information",
        }
    )


@app.route("/favicon.ico")
def favicon():
    """Static favicon covering the above info page"""
    return send_from_directory("static/img", "favicon.ico")


@app.route("/api/v1/discover")
def list_content_types():
    """Returns all configured content type folders"""
    folders = current_app.config["folders"]

    return jsonify(
        {"ok": True, "content_types": list({"name": name} for name in folders.keys())}
    )


@app.route("/api/v1/<content_type>/listing")
def content_type_listing(content_type: str):
    """
    Given a valid content type we return a listing of all folders underneath it
    Also respecting configured search depth
    """
    folders = current_app.config["folders"]

    content_folder = folders.get(content_type)

    if content_folder is None:
        return (
            jsonify({"ok": False, "msg": "Provided content_type is not monitored"}),
            400,
        )

    search_depth = content_folder.depth + 1

    if not content_folder.path.exists():
        return (
            jsonify({"ok": False, "msg": "Provided content_type does not exist"}),
            400,
        )

    folders = []

    search_glob = "/".join("*" * search_depth)

    for content in content_folder.path.glob(search_glob):
        if not content.is_dir():
            # We're only interested in folders
            continue

        if content.name.startswith(".st"):
            # We skip the syncthing specific folders
            continue

        folders.append(
            {
                "name": content.name,
                "size_megabytes": round(
                    sum(f.stat().st_size for f in content.glob("**/*") if f.is_file())
                    / 1024
                    / 1024,
                    2,
                ),
            }
        )

    return jsonify(
        {
            "ok": True,
            "folders": sorted(folders, key=lambda x: x["name"]),
        }
    )


@app.route("/api/v1/<content_type>/stignore")
def stignore_listing(content_type: str):
    """
    Given a valid content type we return the .stignore files contents
    """
    folders = current_app.config["folders"]

    content_folder = folders.get(content_type)

    if content_folder is None:
        return (
            jsonify({"ok": False, "msg": "Provided content_type is not monitored"}),
            400,
        )

    stignore = content_folder.path / ".stignore"

    if not stignore.exists():
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": ".stignore doesn't exists for the provided content_type",
                }
            ),
            400,
        )

    return jsonify(
        {
            "ok": True,
            "entries": load_stignore_file(stignore),
        }
    )


@app.route("/api/v1/<content_type>/stignore", methods=["POST"])
def stignore_modification(content_type: str):
    """
    Apply a modification to the stignore file
    We do not perform any 'cleanup' associated with the modification
    Calling the flush endpoint will trigger that
    """
    folders = current_app.config["folders"]

    content_folder = folders.get(content_type)

    if content_folder is None:
        return (
            jsonify({"ok": False, "msg": "Provided content_type is not monitored"}),
            400,
        )

    stignore = content_folder.path / ".stignore"

    if not stignore.exists():
        return jsonify(
            {
                "ok": False,
                "msg": ".stignore doesn't exists for the provided content_type",
            }
        )

    entries = load_stignore_file(stignore)
    raw_entries = [e["raw"] for e in entries]

    # Insert the payload
    payload = request.get_json(force=True)

    if "actions" not in payload:
        return jsonify({"ok": False, "msg": "No provided actions"})

    actions = load_actions(payload["actions"])

    if not actions["ok"]:
        return jsonify(actions)

    for entry in actions["remove"]:
        if entry in raw_entries:
            raw_entries.remove(entry)

    for entry in actions["add"]:
        if entry not in raw_entries:
            raw_entries.append(entry)

    # Write out new stignore file
    raw_entries.sort()
    stignore.write_text("\n".join(raw_entries) + "\n")

    return jsonify({"ok": True, "msg": "Actions applied"})


@app.route("/api/v1/<content_type>/stignore/flush")
def stignore_flush_report(content_type: str):
    """
    Prepare a list of actions that would occur if a flush was to happen
    This is a fail safe for the user to verify what *would* happen
    """
    folders = current_app.config["folders"]

    content_folder = folders.get(content_type)

    if content_folder is None:
        return (
            jsonify({"ok": False, "msg": "Provided content_type is not monitored"}),
            400,
        )

    stignore = content_folder.path / ".stignore"

    if not stignore.exists():
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": ".stignore doesn't exist for the provided content_type",
                }
            ),
            400,
        )

    entries = load_stignore_file(stignore)
    actions = stignore_actions(entries, content_folder.path)

    return jsonify(
        {
            "ok": True,
            "actions": actions,
        }
    )


@app.route("/api/v1/<content_type>/stignore/flush", methods=["POST"])
def stignore_flush_delete(content_type: str):
    # pylint: disable=too-many-branches
    """
    Flush the stignore file by performing all operations marked in it
    This is mainly used to clean up all folders we've marked to ignore
    """
    folders = current_app.config["folders"]

    content_folder = folders.get(content_type)

    if content_folder is None:
        return (
            jsonify({"ok": False, "msg": "Provided content_type is not monitored"}),
            400,
        )

    stignore = content_folder.path / ".stignore"

    if not stignore.exists():
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": ".stignore doesn't exists for the provided content_type",
                }
            ),
            400,
        )

    payload = request.get_json(force=True)
    payload_actions = payload.get("actions")

    if not payload_actions:
        return (
            jsonify({"ok": False, "msg": "Missing 'actions' confirmation"}),
            400,
        )

    entries = load_stignore_file(stignore)
    actions = stignore_actions(entries, content_folder.path)

    if len(actions) != len(payload_actions):
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": "Invalid actions payload validation (invalid length)",
                }
            ),
            400,
        )

    for i, (src, dst) in enumerate(zip(payload_actions, actions), start=1):
        if src.get("name") != dst.get("name"):
            valid = False
        elif src.get("path") != dst.get("path"):
            valid = False
        elif src.get("action") != dst.get("action"):
            valid = False
        elif src.get("size_megabytes") != dst.get("size_megabytes"):
            valid = False
        else:
            valid = True

        if not valid:
            return (
                jsonify(
                    {
                        "ok": False,
                        "msg": f"Invalid actions payload validation (item {i})",
                    }
                ),
                400,
            )

    for action in actions:
        if action["action"] != "delete":
            continue

        shutil.rmtree(action["path"])

    return jsonify(
        {
            "ok": True,
            "actions": actions,
        }
    )
