# Task B1 - Information Gathering

<p align="center">
<img src="https://img.shields.io/badge/categories-Reverse%20Engineering%2C%20Web%20Analysis-informational">
<img src="https://img.shields.io/badge/points-10-success">
<img src="https://img.shields.io/badge/tools-Firefox%20devtools-blueviolet">
</p>

> The attacker left a file with a ransom demand, which points to a site where they're demanding payment to release the victim's files.
>
> We suspect that the attacker may not have been acting entirely on their own. There may be a connection between the attacker and a larger ransomware-as-a-service ring.
>
> Analyze the demand site, and see if you can find a connection to another ransomware-related site.
>
> Downloads:
>
> - [Demand note from the attacker (YOUR_FILES_ARE_SAFE.txt)](./provided/YOUR_FILES_ARE_SAFE.txt)
>
> Prompt:
>
> - Enter the domain name of the associated site.

## Solution

Obviously the first thing to do would be to inspect the provided ransom note, which has a website in it among other things: https://joxlmnswxaxypbeq.unlockmyfiles.biz/. It looks something like this:

<div style="text-align: center;">
    <img src="./img/initial%20ransom%20website.png" alt="Ransom demand website screenshot">
</div>

Guess it's been a while since this ransomware attack if there's -176 days until the encryption key is deleted. One thing I noticed though was that the deletion timer isn't there initially, so the time must be obtained after the initial page load. Since we're looking for a connection to another ransomware site, I decided to open up the network section of Firefox's devtools to see if there were any connections and lo and behold:

<div style="text-align: center;">
    <img src="./img/Firefox%20devtools%20with%20connection%20to%20other%20website.png" alt="Firefox DevTools open showing connection to another website">
</div>

Actually opening up the website just shows some JSON, but it's still another website. Submitting `iulplkticahjbflq.ransommethis.net` ended up being correct for the other ransomware-related site.
