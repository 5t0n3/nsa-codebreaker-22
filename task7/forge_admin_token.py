import datetime

import jwt

HMAC_KEY = "xqDxTAQBYw4hEsK8ud3ASezUM4IohDW1"

if __name__ == "__main__":
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    admin_jwt = {
        "iat": now,
        "exp": now + datetime.timedelta(days=365),
        "sec": "TQ9mpDdETkLCarLuyggyK8eDvJYESLjA",
        "uid": 16498,
    }

    print(jwt.encode(admin_jwt, HMAC_KEY, algorithm="HS256"))
