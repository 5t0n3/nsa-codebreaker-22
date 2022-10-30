# Task 5 - Core Dumped

<p align="center">
<img src="https://img.shields.io/badge/categories-Reverse%20Engineering%2C%20Cryptography-informational">
<img src="https://img.shields.io/badge/points-500-success">
<img src="https://img.shields.io/badge/tools-gdb%2C%20gcc%2C%20python%2C%20openssl-blueviolet">
</p>

> The FBI knew who that was, and got a warrant to seize their laptop. It looks like they had an encrypted file, which may be of use to your investigation.
>
> We believe that the attacker may have been clever and used the same RSA key that they use for SSH to encrypt the file. We asked the FBI to take a core dump of ssh-agent that was running on the attacker's computer.
>
> Extract the attacker's private key from the core dump, and use it to decrypt the file.
>
> *Hint: if you have the private key in PEM format, you should be able to decrypt the file with the command openssl pkeyutl -decrypt -inkey privatekey.pem -in data.enc*
>
> Downloads:
>
> - [Core dump of ssh-agent from the attacker's computer (core)](./provided/core)
> - [ssh-agent binary from the attacker's computer. The computer was running Ubuntu 20.04. (ssh-agent)](./provided/ssh-agent)
> - [Encrypted data file from the attacker's computer (data.enc)](./provided/data.enc)
>
> Prompt:
>
> - Enter the token value extracted from the decrypted file.

## Solution

I thought it was weird that the attacker's computer was explicitly stated to be running Ubuntu 20.04, and luckily I had a matching VM set up already that I could use for this task. Since I didn't really know where to start, the first thing I did was run `file` on the provided ssh-agent executable and core dump:

```shell
$ file ssh-agent
ssh-agent: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=3734cf9330cd22aab10a4b215b8bcf789f0c6aeb, for GNU/Linux 3.2.0, stripped

$ file core
core: ELF 64-bit LSB core file, x86-64, version 1 (SYSV), SVR4-style, from 'ssh-agent', real uid: 0, effective uid: 0, real gid: 0, effective gid: 101, execfn: '/usr/bin/ssh-agent', platform: 'x86_64'
```

The binary's stripped, which isn't surprising but also isn't helpful if I wanted to, say, use Ghidra to analyze it. Luckily ssh-agent is part of OpenSSH though, which as its name implies is open-source. I browsed its [GitHub repository](https://github.com/openssh/openssh-portable) pretty extensively to begin with and learned a lot about how OpenSSH (well, mostly ssh-agent) works. The most relevant part which I'll describe is how private keys are stored in memory when ssh-agent is running.

### Aside: How ssh-agent stores private keys in memory

When ssh-agent first starts up, it creates an `idtable` struct (shown below) and assigns it to `idtab`:

```c
struct idtable {
    int nentries;
    TAILQ_HEAD(idqueue, identity) idlist;
};
```

This is essentially a linked list structure, where each item (in this case each identity) stores a reference to the next one.

The `identity` struct represents a stored key as well as some other information, like the comment:

```c
typedef struct identity {
    TAILQ_ENTRY(identity) next;
    struct sshkey *key;
    char *comment;
    char *provider;
    time_t death;
    u_int confirm;
    char *sk_provider;
    struct dest_constraint *dest_constraints;
    size_t ndest_constraints;
} Identity;
```

The `sshkey` struct stored in the `key` field is what we care about and represents the actual loaded key:

```c
struct sshkey {
    int type;
    int flags;
    /* KEY_RSA */
    RSA *rsa;
    /* KEY_DSA */
    DSA *dsa;
    /* KEY_ECDSA and KEY_ECDSA_SK */
    int  ecdsa_nid; /* NID of curve */
    EC_KEY *ecdsa;
    /* KEY_ED25519 and KEY_ED25519_SK */
    u_char *ed25519_sk;
    u_char *ed25519_pk;
    /* KEY_XMSS */
    char *xmss_name;
    char *xmss_filename; /* for state file updates */
    void *xmss_state; /* depends on xmss_name, opaque */
    u_char *xmss_sk;
    u_char *xmss_pk;
    /* KEY_ECDSA_SK and KEY_ED25519_SK */
    char *sk_application;
    uint8_t sk_flags;
    struct sshbuf *sk_key_handle;
    struct sshbuf *sk_reserved;
    /* Certificates */
    struct sshkey_cert *cert;
    /* Private key shielding */
    u_char *shielded_private;
    size_t shielded_len;
    u_char *shield_prekey;
    size_t shield_prekey_len;
};
```

That's a lot of fields, but the only ones we really care about for this task are the ones related to shielding the private key.

What's that, you may ask? Well, [this blog post](https://xorhash.gitlab.io/xhblog/0010.html) probably describes it better than I ever could, but at a high level all loaded private keys are stored encrypted in the `shield*` fields of the above struct. As for its purpose, again that blog post puts it better than I can:

> SSH key shielding is a measure intended to protect private keys in RAM against attacks that abuse bugs in speculative execution that current CPUs exhibit.

That went pretty much entirely over my head so I mostly ignored it while doing task 5, but Wikipedia has [an article](https://en.wikipedia.org/wiki/Speculative_execution) about speculative execution if you're curious.

### Obtaining the private key

All that is to say, ssh-agent has to be able to *decrypt* a key that's shielded in memory, which is done through the `sshkey_unshield_private()` function. After unshielding the private key, we have to save it to a file in order to decrypt the provided file. [This blog post](https://security.humanativaspa.it/openssh-ssh-agent-shielded-private-key-extraction-x86_64-linux/) describes basically exactly how to do this. The general process is as follows:

1. Locate and dump the shielded key data
1. Load the shielded key data into memory in a running `ssh-keygen` process
1. Save the private key to a file
1. ???
1. Profit

Unfortunately the blog post requires a running ssh-agent process with the key added in order to extract the shielded key data, but luckily that isn't the only way to obtain it. I think my most important realization for this task was that OpenSSH was open source, so I could actually compile it myself to get the debug symbols back, which would make getting e.g. the shielded key information way easier. On my Ubuntu 20.04 VM I checked the version of OpenSSH I had installed, since it should theoretically match the attacker's OpenSSH version:

```shell
$ ssh -V
OpenSSH_8.2p1 Ubuntu-4ubuntu0.4, OpenSSL 1.1.1f  31 Mar 2020
```

OpenSSH 8.2p1, got it. I then downloaded the correct version of OpenSSH portable from [here](https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/) and extracted it. I actually had to compile two different things with debug symbols: `ssh-agent` and `ssh-keygen`. The debug symbols for `ssh-agent` are what make finding the attacker's (shielded) SSH key much easier, since you can access them like `idtab->idlist->...` with known variable names rather than trying to find their addresses in memory. `ssh-keygen`, on the other hand, is used to save the SSH key to a file for use in decrypting `data.enc`, since the `sshkey_save_private()` function isn't available in the `ssh-agent` executable. Here are the commands for compiling those two things with debug symbols (they need to be run from the extracted `openssh-8.2p1` directory):

```shell
$ ./configure --with-audit=debug
$ make ssh-agent
$ make ssh-keygen
```

Initially I tried loading the compiled `ssh-agent` executable into gdb with the provided core file, but got errors about a mismatch between the two. Eventually I realized that I had to extract only the debug symbols from the compiled `ssh-agent` binary and load them up in gdb separately. This can be done by running the following command:

```shell
$ objcopy --only-keep-debug ssh-agent ssh-agent.dbg
```

They can then be loaded into gdb by running `symbol-file ssh-agent.dbg` within a debug session. Using the information mentioned above, we can actually dump the shielded key memory to files using [the `dump` command](https://sourceware.org/gdb/onlinedocs/gdb/Dump_002fRestore-Files.html):

```shell
(gdb) dump binary memory shielded_private idtab->idlist->tqh_first->key->shielded_private idtab->idlist->tqh_first->key->shielded_private+1392

(gdb) dump binary memory shield_prekey idtab->idlist->tqh_first->key->shield_prekey idtab->idlist->tqh_first->key->shield_prekey+16384
```

Note that 1392 and 16384 are the values of the key's `shielded_len` and `shield_prekey_len` fields, respectively.

Unfortunately you have to manually specify the start/end addresses (the \[value\]+1392/16384 arguments), since just trying to dump the values directly only dumps the first few bytes.

Now that we have the shielded key data & metadata, we can load it up in an `ssh-keygen` process in gdb using the executable with debug symbols we compiled earlier! I adapted the process mostly verbatim from [the blog post I keep mentioning](https://security.humanativaspa.it/openssh-ssh-agent-shielded-private-key-extraction-x86_64-linux/) with a couple changes in [reproduce_key.py](./solving/reproduce_key.py). I just put it in a Python script so that all you have to do is run `source reproduce_key.py` and the key will be unshielded and saved automagically :)

Aside from naming, the biggest difference between `reproduce_key.py` and the blog post's series of commands is the function call to save the SSH key to a file:

```diff
- call sshkey_save_private(*kp, "/tmp/plaintext_private_key", "", "comment", 0, "\x00", 0)
+ call sshkey_save_private($key, "privkey", "", "S3TEhAVX2n04iIQKeHVscw", SSHKEY_PRIVATE_PKCS8, openssh_format_cipher, rounds)
```

The signature of the `sshkey_save_private()` function is the following:

```c
int
sshkey_save_private(struct sshkey *key, const char *filename,
    const char *passphrase, const char *comment,
    int format, const char *openssh_format_cipher, int openssh_format_rounds)
{
    // --snip--
}
```

I'll run through the differences argument by argument:

#### `key`

I avoided having to traverse stack frames, so this is technically just a naming difference.

#### `filename`

This is literally just a naming difference, you could have the filename be anything.

#### `passphrase`

These are actually the same because including a passphrase actually encrypts the private key on disk which we don't want.

#### `comment`

This doesn't actually matter, but I recovered the comment from the original key because I felt like it. This was obtained by running `print idtab->idlist->tqh_first->comment` in gdb while debugging the `ssh-agent` executable.

#### `format`

There are multiple different private key formats, it turns out. The default SSH2 format that OpenSSH uses is incompatible with OpenSSL, so you have to specify the PKCS8 format which is compatible with OpenSSL. This took me a while to figure out, but [this Server Fault answer](https://serverfault.com/a/950686) helped me realize that the different formats existed. Other options for the key format are defined [here](https://github.com/openssh/openssh-portable/blob/27267642699342412964aa785b98afd69d952c88/sshkey.h#L99-L103).

#### `openssh_format_cipher`/`openssh_format_rounds`

Similar to `format`, except these constants have the same values as the blog post function call; I just mirrored the call to this function [here](https://github.com/openssh/openssh-portable/blob/f6d3ed9a8a9280cbb68d6a499850cfe810e92bd0/ssh-keygen.c#L1120) within the OpenSSH codebase itself.

Definitions: [here](https://github.com/openssh/openssh-portable/blob/f6d3ed9a8a9280cbb68d6a499850cfe810e92bd0/ssh-keygen.c#L165) for `openssh_format_cipher` and [here](https://github.com/openssh/openssh-portable/blob/f6d3ed9a8a9280cbb68d6a499850cfe810e92bd0/ssh-keygen.c#L168) for `rounds`.

After all of that, you should have the attacker's private key in the `privkey` file.

### Decrypting `data.enc`

Now for the fun part: decrypting the encrypted data file. This was honestly probably the easiest part of this task since you only need to run a single command that's provided to you in the prompt:

```shell
$ openssl pkeyutl -decrypt -inkey privkey -in data.enc
# Netscape HTTP Cookie File
iulplkticahjbflq.ransommethis.net       FALSE   /       TRUE    2145916800      tok     eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NTM1OTMzMDgsImV4cCI6MTY1NjE4NTMwOCwic2VjIjoiMXVUMTUza1VITU1IcnFxcUVLYWswS1NxeVM0dmR3VGkiLCJ1aWQiOjI2OTYwfQ.sZsTU8onwizKjCuZj99coyuM7wY7QZSWllb9SMAt6BM
```

A cookie file, huh? Submitting the "eyJ0e..." token proves this to be correct (alongside the file obviously being valid text of course :) ).

## Useful Resources

- [Blog post about how OpenSSH shields keys in memory](https://xorhash.gitlab.io/xhblog/0010.html)
- [A blog post about unshielding SSH private keys present in core dumps](https://security.humanativaspa.it/openssh-ssh-agent-shielded-private-key-extraction-x86_64-linux/)
- [Server Fault post about converting OpenSSH keys between formats](https://serverfault.com/a/950686)

## Further Reading

- [Some information about the OpenSSH private key format](https://coolaj86.com/articles/the-openssh-private-key-format/)
- [RFC 5208](https://datatracker.ietf.org/doc/html/rfc5208), which defined the PKCS #8 private key format (among other things)
