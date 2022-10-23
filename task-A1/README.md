# Task A1 - Initial Access

> We believe that the attacker may have gained access to the victim's network by phishing a legitimate users credentials and connecting over the company's VPN. The FBI has obtained a copy of the company's VPN server log for the week in which the attack took place. Do any of the user accounts show unusual behavior which might indicate their credentials have been compromised?
>
> Note that all IP addresses have been anonymized.
>
> Downloads:
>
> - [Access log from the company's VPN server for the week in question. (vpn.log)](./provided/vpn.log)
>
> Prompt:
>
> - Enter the username which shows signs of a possible compromise

# Solution

I ended up using [Miller](https://github.com/johnkerl/miller) to manipulate the CSV log file, but you could just as easily use something like Excel or even [Python's native csv module](https://docs.python.org/3/library/csv.html). The log file has a few columns that are common between all of the entries (including `Proto` and `Node`), so I removed them using Miller. I also removed the IP columns since it was mentioned that all of the addresses were anonymized, so I didn't think they'd be necessary. The result of these cuts was [vpn-stripped.log](./vpn-stripped.log), which was a bit more manageable in my opinion.

Initially I focused pretty heavily on the entries with errors, which came in two flavors: invalid LDAP credentials and when a user wasn't found. I didn't end up finding any patterns when doing that though, so I ended up sorting by users on a whim. Then I noticed something interesting:

```csv
Rebecca.L,2022.03.31 10:01:29 EDT,19809,1,554255820,
Rebecca.L,2022.03.31 11:33:20 EDT,20797,1,3111002433,
```

None of the other users that I saw logged in twice within a single day, and the fact that the two sessions were overlapping was especially suspicious. I then submitted `Rebecca.L` as a username which turned out to be correct.
