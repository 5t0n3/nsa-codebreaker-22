# Set breakpoints & start program
gdb.execute("break main")
gdb.execute("break sshkey_free")
gdb.execute("run")

# Create key struct
gdb.execute("set $key = (struct sshkey *)sshkey_new(0)")

# Read shielded private key from file
gdb.execute('set $shielded_private = (unsigned char *)malloc(1392)')
gdb.execute('set $fd = fopen("shielded_private", "r")')
gdb.execute('call fread($shielded_private, 1, 1392, $fd)')
gdb.execute('call fclose($fd)')
gdb.execute('set $key->shielded_private = $shielded_private')
gdb.execute('set $key->shielded_len = 1392')

# Read shielding prekey from file
gdb.execute('set $shield_prekey = (unsigned char *)malloc(16384)')
gdb.execute('set $fd = fopen("shield_prekey", "r")')
gdb.execute('call fread($shield_prekey, 1, 16384, $fd)')
gdb.execute('call fclose($fd)')
gdb.execute('set $key->shield_prekey = $shield_prekey')
gdb.execute('set $key->shield_prekey_len = 16384')

# Actually unshield the private key
# The try/except is necessary because a breakpoint is hit which throws an error
try:
    gdb.execute("call sshkey_unshield_private($key)")
except:
    pass

# For whatever reason a continue is necessary to finish unshielding the key
gdb.execute("continue")
gdb.execute('call sshkey_save_private($key, "privkey", "", "S3TEhAVX2n04iIQKeHVscw", SSHKEY_PRIVATE_PKCS8, openssh_format_cipher, rounds)')
