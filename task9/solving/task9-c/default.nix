{ stdenv, openssl_3 }:

stdenv.mkDerivation {
  pname = "bruteforce-c";
  version = "0.0.1";

  src = ./.;

  buildInputs = [ openssl_3.dev ];

  # dontStrip = true;

  buildPhase = ''
    $CC -Wall -O2 -g task9.c -o task9-c -lcrypto
  '';

  installPhase = ''
    install -D -m 555 task9-c $out/bin/task9-c
  '';
}
