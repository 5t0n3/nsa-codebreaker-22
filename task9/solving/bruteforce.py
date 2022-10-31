import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# IV -> first 32 hex characters of important_data.pdf.enc
IV = b"\xc1\x50\x45\xf9\x98\x59\xd5\xca\x93\x86\x17\xeb\xc4\x92\x32\x14"

# test block -> first block of encrypted PDF data after IV
TEST_BLOCK = b"\xe3\x41\x05\x64\x35\x08\x56\x6b\x9f\x5e\x51\x6c\x25\xcc\x8c\x8e"

# keys are truncated to first 16 characters of UUID
KEY_BASE = "{:x}-b0fb-11"

# All PDF files start with this byte sequence
PDF_MAGIC = b"%PDF"

def test_key(time_seq):
    global KEY_BASE, IV, TEST_BLOCK

    # generate key based on aforementioned format
    key = KEY_BASE.format(time_seq).encode()

    # attempt decrypting the test block
    cipher = Cipher(algorithms.AES(key), modes.CBC(IV))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(TEST_BLOCK) + decryptor.finalize()

    return decrypted

if __name__ == "__main__":
    keys_tested = 0
    start_time = time.perf_counter()
    result_found = False

    # 12 seconds before: de082b80-b0fb-11
    # 1 second before: e52f8980-b0fb-11

    for seq in range(0xde082b80, 0xe52f8980):
        result = test_key(seq)
        keys_tested += 1

        if result.startswith(PDF_MAGIC):
            result_found = True
            break

        if keys_tested % 1000000 == 0:
            print(f"{keys_tested} keys tested")

    end_time = time.perf_counter()

    print("\n=====================================================================")

    if result_found:
        print(b"decrypted block: " + result)
        print("key: " + KEY_BASE.format(seq))
    else:
        print("no key found")

    print(f"seconds elapsed: {end_time - start_time}")
