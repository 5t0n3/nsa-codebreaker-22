{
  # TODO: bump this to 22.11
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
  inputs.crane = {
    url = "github:ipetkov/crane";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, crane }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      craneLib = crane.lib.${system};
      bruteforce-rs = craneLib.buildPackage {
        src = craneLib.cleanCargoSource ./task9/solving/bruteforce-rs;
      };
      inherit (pkgs) mkShell python310 miller;
    in {
      packages.${system} = { inherit bruteforce-rs; };

      devShells.${system} = {
        task-a1 = mkShell { packages = [ miller ]; };

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

