{
  description = "A tool for viewing and editing your nix configuration as a tree";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { self, nixpkgs, poetry2nix }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system}.extend poetry2nix.overlays.default;
      lib = nixpkgs.lib;
      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
    in
    {
      defaultPackage.x86_64-linux = mkPoetryApplication {
          type = "app";
          projectDir = ./.;

          nativeBuildInputs = [
            pkgs.inconsolata-nerdfont
          ];

          # To copy over the full options json
          preInstall = ''
            mkdir -p $out/data
            cp ./data/options.json $out/data
          '';

          meta = {
            description = "A tool for viewing and editing your nix configuration as a tree";
            homepage = "https://github.com/max-amb/nix-tree";
            license = lib.licenses.gpl3;
            maintainers = with lib.maintainers; [ max-amb ];
            platforms = lib.platforms.linux;
          };
      };

    };
}
