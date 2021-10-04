import json

import pytest


def test_stignore_add_entries(agent):
    # Create the .stignore file
    stignore_path = agent.config["base_folder"] / "share-1" / ".stignore"
    stignore_path.write_text("")

    actions = [
        {
            "action": "add",
            "type": "ignore",
            "name": "Object 1",
        },
        {
            "action": "add",
            "type": "keep",
            "name": "Object 2",
        },
    ]

    response = agent.client.post("/api/v1/share-1/stignore", json={"actions": actions})
    assert response.status == "200 OK"

    expected_entries = sorted(
        [
            "Object 1/",
            "!Object 2/",
        ]
    )

    actual_entries = [
        entry for entry in stignore_path.read_text().split("\n") if entry != ""
    ]

    assert expected_entries == actual_entries


def test_stignore_remove_entries(agent):
    # Create the .stignore file
    stignore_path = agent.config["base_folder"] / "share-1" / ".stignore"
    stignore_path.write_text("!Object 1/\nObject 2/\nObject 3/\n")

    actions = [
        {
            "action": "remove",
            "type": "ignore",
            "name": "Object 2",
        },
        {
            "action": "remove",
            "type": "keep",
            "name": "Object 1",
        },
    ]

    response = agent.client.post("/api/v1/share-1/stignore", json={"actions": actions})
    assert response.status == "200 OK"

    expected_entries = sorted(
        [
            "Object 3/",
        ]
    )

    actual_entries = [
        entry for entry in stignore_path.read_text().split("\n") if entry != ""
    ]

    assert expected_entries == actual_entries
