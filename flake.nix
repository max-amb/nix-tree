{
  # Description of the application
  description = "A tool for viewing and editing your nix configuration as a tree";

  # Importing nixpkgs (the package repository) and poetry for building the application
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { self, nixpkgs, poetry2nix }:
    let
      # Setting system to 64 bit linux
      system = "x86_64-linux";

      # Adding poetry to our nixpkgs, and setting the pkgs variable as this
      pkgs = nixpkgs.legacyPackages.${system}.extend poetry2nix.overlays.default;

      # Setting the lib variable (for licenses and maintainers)
      lib = nixpkgs.lib;

      # Extract mkPoetryApplication from mkPoetry2Nix for buikding our application
      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
    in
    {
      # The section that builds our application
      defaultPackage.x86_64-linux = mkPoetryApplication {
          type = "app";

          # The project is found at the root of the repository
          projectDir = ./.;

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
