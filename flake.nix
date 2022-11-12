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
      task9-rs = craneLib.buildPackage {
        src = craneLib.cleanCargoSource ./task9/solving/task9-rs;
      };
      task9-c = pkgs.callPackage ./task9/solving/task9-c { };
      taskPython = pkgs.python310.withPackages (nixpkgs.lib.attrVals [
        "requests"
        "pyjwt"
        "beautifulsoup4"
        "cryptography"
      ]);
      inherit (pkgs) mkShell python310 miller;
    in {
      packages.${system} = { inherit task9-rs task9-c; };

      # TODO: consolidate python devshells? no reason to keep them separated
      devShells.${system}.default =
        mkShell { packages = [ miller taskPython task9-rs task9-c ]; };

      formatter.${system} = pkgs.nixfmt;
    };
}

