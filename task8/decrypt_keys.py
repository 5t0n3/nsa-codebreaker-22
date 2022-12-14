from base64 import b64decode
import sqlite3

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEY_ENCRYPTION_KEY = b64decode("Y0cMBiqsoL9TcLV39AOjMVpTaJJJSEYHVBxQcGYudmg=")


def decrypt_key(enc_base64):
    decoded = b64decode(enc_base64)
    iv, encrypted = decoded[:16], decoded[16:]

    cipher = Cipher(algorithms.AES(KEY_ENCRYPTION_KEY), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()

    # decryption adds padding that we need to remove
    return decrypted[:32].decode()


if __name__ == "__main__":
    with sqlite3.connect("recovered/keyMaster.db") as con:
        key_result = con.execute("SELECT customerId, encryptedKey FROM customers")
        encrypted_keys = key_result.fetchall()

    decrypted_keys = [f"{cid} -> {decrypt_key(key)}" for cid, key in encrypted_keys]

    with open("decrypted-keys.txt", "w") as f:
        f.write("\n".join(decrypted_keys))
