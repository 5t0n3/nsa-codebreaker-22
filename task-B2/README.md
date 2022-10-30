# Task B2 - Getting Deeper

<p align="center">
<img src="https://img.shields.io/badge/categories-Web%20Hacking%2C%20%5Bredacted%5D-informational">
<img src="https://img.shields.io/badge/points-100-success">
<img src="https://img.shields.io/badge/tools-git%2C%20python-blueviolet">
</p>

> It looks like the backend site you discovered has some security features to prevent you from snooping. They must have hidden the login page away somewhere hard to guess.
>
> Analyze the backend site, and find the URL to the login page.
>
> Hint: this group seems a bit sloppy. They might be exposing more than they intend to.
>
> Warning: Forced-browsing tools, such as DirBuster, are unlikely to be very helpful for this challenge, and may get your IP address automatically blocked by AWS as a DDoS-prevention measure. Codebreaker has no control over this blocking, so we suggest not attempting to use these techniques.
>
> Prompt:
>
> - Enter the URL for the login page

## Solution

Don't use DirBuster, noted. I initially didn't know where to start for this one, so I tried just navigating to the `/login` page, but only got a screen that said "Unauthorized." I then decided to look at all the information I got from the website I discovered in the previous task (https://iulplkticahjbflq.ransommethis.net/demand?cid=64187). There's only 3 fields in the JSON returned: `address`, `amount`, and `exp_date`, so nothing interesting. When I looked at the headers, I saw something interesting: a header called `x-git-commit-hash`. I thought that was interesting, so I tried navigating to https://iulplkticahjbflq.ransommethis.net/.git:

<div align="center">
    <img src="./img/directory%20listing%20disabled.png" alt="Directory listing disabled screen">
</div>

Huh, that's different. Navigating to `/.git/index` prompted me to download a file, so that means that the entire Git repository for this website is exposed.

I decided to stick the `index` file inside of an empty `.git` repository and ran `git diff` to see what would happen:

```shell
$ git diff
fatal: unable to read fc46c46e55ad48869f4b91c2ec8756e92cc01057
```

Huh, that kinda looks like an object hash. After doing some research I found out about the [`git ls-files`](https://git-scm.com/docs/git-ls-files) command which, when passed the `--stage` flag, prints out all of the objects and filenames currently in the index:

```shell
$ git ls-files --stage
100755 fc46c46e55ad48869f4b91c2ec8756e92cc01057 0       Dockerfile
100755 dd5520ca788a63f9ac7356a4b06bd01ef708a196 0       Pipfile
100644 47709845a9b086333ee3f470a102befdd91f548a 0       Pipfile.lock
100755 e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 0       app/__init__.py
100644 d236c9b561a6a15493be524958e6d415ca040e61 0       app/server.py
100755 a844f894a3ab80a4850252a81d71524f53f6a384 0       app/templates/404.html
100644 1df0934819e5dcf59ddf7533f9dc6628f7cdcd25 0       app/templates/admin.html
100644 b9cfd98da0ac95115b1e68967504bd25bd90dc5c 0       app/templates/admininvalid.html
100644 bb830d20f197ee12c20e2e9f75a71e677c983fcd 0       app/templates/adminlist.html
100644 5033b3048b6f351df164bae9c7760c32ee7bc00f 0       app/templates/base.html
100644 10917973126c691eae343b530a5b34df28d18b4f 0       app/templates/forum.html
100644 fe3dcf0ca99da401e093ca614e9dcfc257276530 0       app/templates/home.html
100644 779717af2447e24285059c91854bc61e82f6efa8 0       app/templates/lock.html
100644 0556cd1e1f584ff5182bbe6b652873c89f4ccf23 0       app/templates/login.html
100644 56e0fe4a885b1e4eb66cda5a48ccdb85180c5eb3 0       app/templates/navbar.html
100755 ed1f5ed5bc5c8655d40da77a6cfbaed9d2a1e7fe 0       app/templates/unauthorized.html
100644 c980bf6f5591c4ad404088a6004b69c412f0fb8f 0       app/templates/unlock.html
100644 470d7db1c7dcfa3f36b0a16f2a9eec2aa124407a 0       app/templates/userinfo.html
100644 a52a329b6b949bc1bbaacfa35f095831424447dc 0       app/util.py
```

Whoa that's a lot of files! I guess this website is being served by some sort of Python web server in a docker container. For some reason I knew how Git stores objects, but essentially (unless you run the `git repack` command) all Git objects are stored in `.git/objects/<first two digits of hash>/<rest of hash>`, which based on the above output would be `.git/objects/fc/46c46e55ad48869f4b91c2ec8756e92cc01057` for the Dockerfile (more information about how Git stores objects can be found in [this chapter](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects) of the Git book). Rather than manually downloading all of those objects, I decided to write up a quick Python script to fetch all of them for me.

Because the `index` file is in a [binary format](https://git-scm.com/docs/index-format), I didn't really feel like figuring out its exact structure so I just copied the hashes in from the result of `git ls-files --stage` and turned them into a list. I used the [`requests`](https://github.com/psf/requests) library to actually fetch the objects from the server, and just had to iterate over the hashes and write them to the proper paths to do so. The results was [`fetch_objects.py`](./fetch_objects.py), which worked well for my purposes (it does have to be run from the same directory as the `.git/` directory though). After running the script, the `git restore "*"` command brings back all of the files, allowing you to browse through the Python source of the ransomware ring website.

I went straight to [`app/server.py`](./server-files/app/server.py), since I figured that'd be where the super secret login URL would be, and I was not disappointed. The very first function declared is one called `expected_pathkey()`, which just returns the string `adrlarozeijppjmg`. Scrolling all the way down to the bottom confirms that you must have the pathkey right after the domain name, or else the web server redirects you to the unauthorized page from earlier. Now that I know the pathkey, I can try appending it to the URL found in the previous task. Navigating to https://iulplkticahjbflq.ransommethis.net/adrlarozeijppjmg yields the following screen:

<div align="center">
    <img src="./img/login%20screen.png" alt="Login screen">
</div>

Success! Submitting `https://iulplkticahjbflq.ransommethis.net/adrlarozeijppjmg/login` as the answer (you're automatically redirected to the login page) proves this to be correct.
