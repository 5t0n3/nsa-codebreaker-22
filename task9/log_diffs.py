from datetime import datetime, timezone
import pathlib
import uuid

LOG_PATH = "../task8/recovered/keygeneration.log"
KEY_FILE = "../task8/decrypted-keys.txt"


def parse_log(log_path):
    with open(log_path, "r") as log:
        log_lines = log.readlines()

    split_lines = [line.split() for line in log_lines]

    # line format: timestamp username cid demand (we only care about timestamp & cid)
    cid_timestamp_map = {
        int(line[2]): datetime.fromisoformat(line[0]) for line in split_lines
    }
    return cid_timestamp_map


def parse_uuids(path):
    with open(path, "r") as f:
        lines = f.readlines()

    split_lines = [line.strip().split(" -> ") for line in lines]

    # the extra 4 zeros have to be added to get a "complete" UUID
    cid_map = {
        int(cid): extract_time(uuid_str + "0000") for cid, uuid_str in split_lines
    }
    return cid_map


def extract_time(uuid_obj):
    if not isinstance(uuid_obj, uuid.UUID):
        uuid_obj = uuid.UUID(uuid_obj)

    time_low, time_mid, time_hi_version = uuid_obj.fields[:3]

    # remove version number
    time_hi = time_hi_version ^ 0x1000

    time_ns = (time_hi << 48) + (time_mid << 32) + time_low

    # convert to unix time (seconds since 1/1/1970) as described in RFC 4122
    unix_time = (time_ns - 0x01B21DD213814000) / 1e7

    return datetime.fromtimestamp(unix_time, timezone.utc)


if __name__ == "__main__":
    # generate a cid -> timestamp mapping from the key generation log
    log_map = parse_log(LOG_PATH)
    key_map = parse_uuids(KEY_FILE)
    diff_map = {}

    for cid, timestamp in key_map.items():
        log_timestamp = log_map[cid]
        diff_map[cid] = (log_timestamp - timestamp).total_seconds()

    diffs = diff_map.values()
    print(f"Maximum log/UUID difference: {max(diffs)} seconds")
    print(f"Minimum log/UUID difference: {min(diffs)} seconds")
