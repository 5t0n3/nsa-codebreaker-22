import datetime

import jwt

EXPIRED = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NTM1OTMzMDgsImV4cCI6MTY1NjE4NTMwOCwic2VjIjoiMXVUMTUza1VITU1IcnFxcUVLYWswS1NxeVM0dmR3VGkiLCJ1aWQiOjI2OTYwfQ.sZsTU8onwizKjCuZj99coyuM7wY7QZSWllb9SMAt6BM"

HMAC_KEY = "xqDxTAQBYw4hEsK8ud3ASezUM4IohDW1"

if __name__ == "__main__":
    # Don't verify if the key is expired (we know it is haha)
    expired_dec = jwt.decode(
        EXPIRED, HMAC_KEY, algorithms=["HS256"], options={"verify_exp": False}
    )

    # Choose valid iat/exp dates
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    expired_dec["iat"] = now
    expired_dec["exp"] = now + datetime.timedelta(days=365)  # 1 year later for leeway

    print(jwt.encode(expired_dec, HMAC_KEY, algorithm="HS256"))
