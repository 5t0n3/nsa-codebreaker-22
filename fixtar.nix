{ stdenv, fetchFromGitHub }:

stdenv.mkDerivation {
  pname = "fixtar";
  version = "git";
  src = fetchFromGitHub {
    owner = "BestSolution-at";
    repo = "fixtar";
    rev = "963c934a8a6b37c408ea9a3c3c01167bc088d036";
    sha256 = "1j34cmsl7k7wfmrngyql6zq3m84jahb0w94w6xsnjbxigg5mxdgl";
  };

  sourceRoot = "source/src";

  installPhase = ''
    install -s -D -m 755 ft $out/bin/ft
  '';
}
