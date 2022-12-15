from datetime import datetime, timedelta
import uuid

LOG_TIMESTAMP = datetime.fromisoformat("2022-03-31T10:07:28-04:00")


def datetime_to_uuid(dt):
    time_unix = dt.timestamp()

    # reverse of RFC 4122 conversion from other script
    time_ns = int(time_unix * 1e7) + 0x01B21DD213814000
    time_low = time_ns & 0xFFFFFFFF
    time_mid = (time_ns >> 32) & 0xFFFF
    time_hi_version = ((time_ns >> 48) & 0x0FFF) | 0x1000

    # last 3 fields are the clock sequence/node which are constant across all of the UUIDs
    key_uuid = uuid.UUID(
        fields=(time_low, time_mid, time_hi_version, 0x85, 0x8B, 0x29CF26A70000)
    )
    return str(key_uuid)[:32]


if __name__ == "__main__":
    upper_bound = datetime_to_uuid(LOG_TIMESTAMP - timedelta(seconds=6))
    lower_bound = datetime_to_uuid(LOG_TIMESTAMP - timedelta(seconds=12))

    print(f"Upper bound UUID (6 seconds before): {upper_bound}")
    print(f"Lower bound UUID (12 seconds before): {lower_bound}")
