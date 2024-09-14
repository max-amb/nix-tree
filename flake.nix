{
  description = "Python application packaged using poetry2nix";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

  outputs = { self, nixpkgs, poetry2nix }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system}.extend poetry2nix.overlays.default;
      myPythonApp = pkgs.poetry2nix.mkPoetryApplication { projectDir = self; };
      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
    in
    {
      defaultPackage.x86_64-linux = mkPoetryApplication {
          projectDir = ./.;
      };

      apps.${system}.default = {
        type = "app";
        # replace <script> with the name in the [tool.poetry.scripts] section of your pyproject.toml
        program = "${myPythonApp}/bin/nix-tree";
      };
    };
}
