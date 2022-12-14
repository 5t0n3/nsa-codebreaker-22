{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.crane = {
    url = "github:ipetkov/crane";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    crane,
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {inherit system;};
    craneLib = crane.lib.${system};
    task9-rs = craneLib.buildPackage {
      src = craneLib.cleanCargoSource ./task9/solving/task9-rs;
    };
    task9-c = pkgs.callPackage ./task9/solving/task9-c {};
    taskPython = pkgs.python310.withPackages (nixpkgs.lib.attrVals [
      "requests"
      "pyjwt"
      "beautifulsoup4"
      "cryptography"
    ]);
    inherit (pkgs) mkShell python310Packages sqlite miller file;
  in {
    packages.${system} = {inherit task9-rs task9-c;};

    devShells.${system} = {
      default = mkShell {packages = [miller file taskPython sqlite task9-rs task9-c];};
      format = mkShell {packages = [python310Packages.mdformat];};
    };

    formatter.${system} = pkgs.alejandra;
  };
}
