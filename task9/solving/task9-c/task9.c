#include <openssl/evp.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

// NOTE: This is like my first C program so sorry if it's like terrible :)

const unsigned char IV[] = {0xc1,0x50,0x45,0xf9,0x98,0x59,0xd5,0xca,0x93,0x86,0x17,0xeb,0xc4,0x92,0x32,0x14};
const unsigned char TEST_BLOCK[] = {0xe3,0x41,0x05,0x64,0x35,0x08,0x56,0x6b,0x9f,0x5e,0x51,0x6c,0x25,0xcc,0x8c,0x8e};
const unsigned char PDF_MAGIC[] = "%PDF";

unsigned char *key, *result;
int outl;

bool test_key(unsigned int time_seq, EVP_CIPHER *cipher, EVP_CIPHER_CTX *ctx) {
    // Create key in UUID format
    sprintf((char *)key, "%x-b0fb-11", time_seq);

    // Initialize AES decryptor
    EVP_DecryptInit_ex2(ctx, cipher, key, IV, NULL);

    // Decryption :) (still don't know why inl has to be 17)
    if (!EVP_DecryptUpdate(ctx, result, &outl, TEST_BLOCK, 17)) {
        printf("error decrypting with key %s\n", key);
        return false;
    }

    // Reset context because you're supposed to apparently
    EVP_CIPHER_CTX_reset(ctx);

    // Check for pdf magic
    return !memcmp(result, PDF_MAGIC, (long unsigned int) 4);
}

int main() {
    // timing because stats or something
    clock_t start_time = clock();

    // OpenSSL initialization
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    EVP_CIPHER *cipher = EVP_CIPHER_fetch(NULL, "AES-128-CBC", NULL);

    // Decryption pointer things
    result = OPENSSL_malloc(EVP_CIPHER_get_block_size(cipher));
    key = OPENSSL_malloc(EVP_CIPHER_get_key_length(cipher));

    bool found_key = false;
    for (unsigned int time = 0xdea0c200; time < 0xe2344900; time++) {
        if (test_key(time, cipher, ctx)) {
            found_key = true;
            break;
        }
    }

    clock_t end_time = clock();

    if (found_key) {
        printf("Key: %s\n", key);
        printf("Decrypted data: %s\n", result);
        printf("Took %.3f seconds to brute force.\n", (double)(end_time - start_time) / CLOCKS_PER_SEC);
    } else {
        printf("No key found.\n");
    }

    // Free cipher/context because C
    EVP_CIPHER_free(cipher);
    EVP_CIPHER_CTX_free(ctx);

    return !found_key;
}
