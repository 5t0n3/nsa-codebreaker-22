# Task A2 - Identifying the attacker

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

# Solution

The first thing I did was extract the contents of `root.tar.bz2`. The most interesting files from there were [`.bash_history`](./root-extracted/.bash_history), [`.cert.pem`](./root-extracted/.cert.pem), and [`runwww.py`](./root-extracted/runwww.py). From `.bash_history`, I saw that the attacker extracted what were presumably their ransomware tools and ran `runwww.py`, which starts an HTTP TLS server using OpenSSL. As part of running that server, the script generates a certificate and stores it in `.cert.pem`, which luckily the attacker never deleted. Using Wireshark, we can actually use this certificate to decrypte the TLS traffic going through the staging server as captured in [`session.pcap`](./provided/session.pcap).

After opening up the packet capture in Wireshark, I followed [a guide on its wiki](https://wiki.wireshark.org/TLS#tls-decryption) to add the RSA private key in `.cert.pem` to allow the TLS traffic to be decrypted. This was the result after doing so:

<div style="text-align: center;">
    <img src="./img/packet%20capture%20post-decryption.png" alt="Wireshark after decrypting the TLS traffic">
</div>

The GET request doesn't contain anything interesting, so I decided to check out the first packet labeled "TLS segment of a reassembled PDU:"

<div style="text-align: center;">
    <img src="./img/decrypted%20contents%20of%20first%20reassembled%20PDU.png" alt="Decrypted contents of first reassembled TLS PDU">
</div>

`AheadProudGlut` doesn't really sound like a username but I decided to submit it anyways and it ended up being correct. Not so sure who came up with that username :)
