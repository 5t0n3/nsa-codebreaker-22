use aes::cipher::{BlockDecryptMut, KeyIvInit};
use hex_literal::hex;
use rayon::prelude::*;
use std::time::Instant;

type Aes128CbcDecryptor = cbc::Decryptor<aes::Aes128>;

const IV: [u8; 16] = hex!("c15045f99859d5ca938617ebc4923214");
const TEST_BLOCK: [u8; 16] = hex!("E3 41 05 64 35 08 56 6B 9F 5E 51 6C 25 CC 8C 8E");

const PDF_MAGIC: &[u8] = "%PDF".as_bytes();
const MAGIC_LEN: usize = 4;

fn test_key(time_chunk: u32) -> Option<(String, [u8; 16])> {
    let key = format!("{:x}-b0fb-11", time_chunk);
    let mut buf = [0u8; 16];

    Aes128CbcDecryptor::new(key.as_bytes().into(), &IV.into())
        .decrypt_block_b2b_mut(&TEST_BLOCK.into(), (&mut buf).into());

    if buf[..MAGIC_LEN] == *PDF_MAGIC {
        Some((key, buf))
    } else {
        None
    }
}

fn main() {
    // 12 seconds before log time: de082b80-b0fb-11
    // 1 second before: e52f3980-b0fb-11

    let start_time = Instant::now();

    if let Some((key, data)) = (0xde082b80..0xe52f3980)
        .into_par_iter()
        .find_map_any(test_key)
    {
        println!("Key: {}", key);
        println!("Decrypted data: {}", String::from_utf8_lossy(&data).escape_debug());
    } else {
        println!("No key found!");
    }

    let elapsed_time = start_time.elapsed();
    println!("Took {:.3} seconds to brute force.", elapsed_time.as_secs_f32());
}
