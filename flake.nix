{
  # TODO: bump this to 22.11
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
  inputs.naersk = {
    url = "github:nix-community/naersk";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, naersk }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      fixtar = pkgs.callPackage ./fixtar.nix { };
      bruteforce-rs = naersk.lib.${system}.buildPackage {
        src = ./task9/solving/bruteforce-rs;
      };
      inherit (pkgs) mkShell python310 miller;
    in {
      packages.${system} = { inherit fixtar bruteforce-rs; };

      devShells.${system} = {
        task-a1 = mkShell { packages = [ miller ]; };

        task-a2 = mkShell { packages = [ fixtar ]; };

        task-b2 = mkShell {
          packages = [ (python310.withPackages (ps: [ ps.requests ])) ];
        };

        tasks6-7 = mkShell {
          packages = [ (python310.withPackages (ps: [ ps.pyjwt ])) ];
        };

        task-9 = mkShell {
          packages = [
            (python310.withPackages (ps: [ ps.cryptography ]))
            bruteforce-rs
          ];
        };
      };

      formatter.${system} = pkgs.nixfmt;
    };
}

