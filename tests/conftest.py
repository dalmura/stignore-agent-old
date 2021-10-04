import os

from types import SimpleNamespace

import pytest
import yaml


from stignore_agent.helpers import parse_config
from stignore_agent.app import app


def junk_binary(megabytes):
    return os.urandom(megabytes * 1024 * 1024)


@pytest.fixture
def agent_setup(tmp_path):
    base_folder = tmp_path / "shares"
    base_folder.mkdir()

    share_1 = base_folder / "share-1"
    share_1.mkdir()

    share_1_folder_1 = share_1 / "Object 1"
    share_1_folder_1.mkdir()

    share_1_folder_1_object_1 = share_1_folder_1 / "File 1"
    share_1_folder_1_object_1.write_bytes(junk_binary(25))

    share_1_folder_2 = share_1 / "Object 2"
    share_1_folder_2.mkdir()

    share_1_folder_2_object_1 = share_1_folder_2 / "File 1"
    share_1_folder_2_object_1.write_bytes(junk_binary(10))

    share_1_folder_2_object_2 = share_1_folder_2 / "File 2"
    share_1_folder_2_object_2.write_bytes(junk_binary(2))

    share_1_folder_3 = share_1 / "Object 3"
    share_1_folder_3.mkdir()

    share_1_folder_3_object_1 = share_1_folder_3 / "File 1"
    share_1_folder_3_object_1.write_bytes(junk_binary(5))

    share_2 = base_folder / "share-2"
    share_2.mkdir()

    share_2_folder_1 = share_2 / "Object 1"
    share_2_folder_1.mkdir()

    share_2_folder_1_sub_1 = share_2_folder_1 / "Sub Object 1"
    share_2_folder_1_sub_1.mkdir()

    share_2_folder_1_sub_1_object_1 = share_2_folder_1_sub_1 / "File 1"
    share_2_folder_1_sub_1_object_1.write_bytes(junk_binary(10))

    share_2_folder_1_sub_2 = share_2_folder_1 / "Sub Object 2"
    share_2_folder_1_sub_2.mkdir()

    share_2_folder_1_sub_2_object_1 = share_2_folder_1_sub_2 / "File 1"
    share_2_folder_1_sub_2_object_1.write_bytes(junk_binary(15))

    share_2_folder_1_sub_3 = share_2_folder_1 / "Sub Object 3"
    share_2_folder_1_sub_3.mkdir()

    share_2_folder_1_sub_3_object_1 = share_2_folder_1_sub_3 / "File 1"
    share_2_folder_1_sub_3_object_1.write_bytes(junk_binary(6))

    share_2_folder_2 = share_2 / "Object 2"
    share_2_folder_2.mkdir()

    share_2_folder_2_sub_1 = share_2_folder_2 / "Sub Object 1"
    share_2_folder_2_sub_1.mkdir()

    share_2_folder_2_sub_1_object_1 = share_2_folder_2_sub_1 / "File 1"
    share_2_folder_2_sub_1_object_1.write_bytes(junk_binary(6))

    share_2_folder_2_sub_2 = share_2_folder_2 / "Sub Object 2"
    share_2_folder_2_sub_2.mkdir()

    share_2_folder_2_sub_2_object_1 = share_2_folder_2_sub_2 / "File 1"
    share_2_folder_2_sub_2_object_1.write_bytes(junk_binary(6))

    yield parse_config(
        {
            "base_folder": str(base_folder),
            "folders": [
                {"name": "share-1"},
                {"name": "share-2", "depth": 1},
            ],
        }
    )


@pytest.fixture
def agent(agent_setup):
    agent_setup["TESTING"] = True

    app.config.update(agent_setup)
    app.testing = True

    yield SimpleNamespace(
        client=app.test_client(),
        config=agent_setup,
    )
