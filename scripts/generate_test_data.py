#!/usr/bin/env python3

import random
import sys
import os

from pathlib import Path

import yaml


def junk_binary(megabytes):
    return os.urandom(megabytes * 1024 * 1024)


def random_range(upper_limit):
    return range(1, random.randint(2, upper_limit + 1))


def junk_files(path, max_files=4):
    for i in random_range(max_files):
        file_path = path / f"File {i}"
        file_path.write_bytes(junk_binary(random.randint(1, 20)))


def random_setup(base_path):
    config = {}
    config["base_folder"] = str(base_path)
    config["folders"] = []

    for ct_num in random_range(5):
        # Content Type
        ct_name = f"Content Type {ct_num}"
        ct_path = base_path / ct_name
        ct_path.mkdir()

        has_subobjects = random.choice([True, False])
            
        config["folders"].append({"name": ct_name, "depth": 1 if has_subobjects else 0})

        for ct_depth_folder in random_range(4):
            # Content Folder
            ct_depth_path = ct_path / f"Object {ct_depth_folder}"
            ct_depth_path.mkdir()

            if not has_subobjects:
                junk_files(ct_depth_path)
                continue

            for ct_depth_sub_folder in random_range(4):
                # Content Sub Folder
                ct_depth_sub_path = ct_depth_path / f"Sub Object {ct_depth_sub_folder}"
                ct_depth_sub_path.mkdir()

                junk_files(ct_depth_sub_path)

    with open(base_path / "config.yml", "wt", encoding="utf-8") as config_file:
        yaml.dump(config, config_file, explicit_start=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("ERROR: Wrong number of arguments")
        print(f"USAGE: {sys.argv[0]} /path/to/base/dir")
        sys.exit(1)

    random_setup(Path(sys.argv[1]))
