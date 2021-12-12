import json

import pytest


def test_stignore_flush_check_does_nothing(agent):
    # Create the .stignore file
    stignore_path = agent.config["base_folder"] / "share-1" / ".stignore"

    # Add in share-1 'Object 5' which doesn't exist locally
    stignore_path.write_text("Object 5/\n")

    response = agent.client.get("/api/v1/share-1/stignore/flush")
    assert response.status == "200 OK"

    data = response.get_json()

    assert data == {"ok": True, "actions": []}


def test_stignore_flush_check_valid(agent):
    # Create the .stignore file
    stignore_path = agent.config["base_folder"] / "share-1" / ".stignore"

    # Add in share-1 'Object 1' which does exist locally
    stignore_path.write_text("Object 1/\n")

    response = agent.client.get("/api/v1/share-1/stignore/flush")
    assert response.status == "200 OK"

    data = response.get_json()

    object_1_path = agent.config["base_folder"] / "share-1" / "Object 1"

    assert data == {
        "ok": True,
        "actions": [
            {
                "name": str(object_1_path.name),
                "path": str(object_1_path),
                "size_megabytes": 25.0,
                "action": "delete",
            },
        ],
    }


def test_stignore_flush_delete_works(agent):
    # Create the .stignore file
    stignore_path = agent.config["base_folder"] / "share-1" / ".stignore"

    # Add in share-1 'Object 1' which does exist locally
    stignore_path.write_text("Object 1/\n")

    # Get the pending actions
    response = agent.client.get("/api/v1/share-1/stignore/flush")
    assert response.status == "200 OK"

    data = response.get_json()

    # Post back the pending actions
    response = agent.client.post("/api/v1/share-1/stignore/flush", json=data)
    assert response.status == "200 OK"

    data = response.get_json()

    object_1_path = agent.config["base_folder"] / "share-1" / "Object 1"

    assert data == {
        "ok": True,
        "actions": [
            {
                "name": str(object_1_path.name),
                "path": str(object_1_path),
                "action": "delete",
                "size_megabytes": 25.0,
            },
        ],
    }

    # Verify 'Object 1' has indeed been deleted
    share_1 = agent.config["base_folder"] / "share-1"

    assert object_1_path not in share_1.iterdir()


def test_stignore_flush_delete_check_works(agent):
    # Create the .stignore file
    stignore_path = agent.config["base_folder"] / "share-1" / ".stignore"

    # Add in share-1 'Object 1' which does exist locally
    stignore_path.write_text("Object 1/\n")

    # Attempt to perform the delete with no payload
    response = agent.client.post("/api/v1/share-1/stignore/flush", json={})
    assert response.status == "400 BAD REQUEST"

    assert response.get_json() == {
        "ok": False,
        "msg": "Missing 'actions' confirmation",
    }

    # Attempt to perform the delete with a different number of items
    response = agent.client.post(
        "/api/v1/share-1/stignore/flush", json={"actions": [{"a": 1}, {"b": 2}]}
    )
    assert response.status == "400 BAD REQUEST"

    assert response.get_json() == {
        "ok": False,
        "msg": "Invalid actions payload validation (invalid length)",
    }

    # Attempt to perform the delete with a different payload
    response = agent.client.post(
        "/api/v1/share-1/stignore/flush",
        json={
            "actions": [
                {
                    "name": "Object 4",
                    "path": "Object 4/",
                    "action": "delete",
                    "size_megabytes": 10.5,
                }
            ]
        },
    )
    assert response.status == "400 BAD REQUEST"

    assert response.get_json() == {
        "ok": False,
        "msg": "Invalid actions payload validation (item 1)",
    }
