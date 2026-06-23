{
  description = "A tool for viewing and editing your nix configuration as a tree";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, pyproject-nix, uv2nix, pyproject-build-systems }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        python = pkgs.python313;

        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

        pythonSet = (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
          nixpkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })
          ]
        );

        virtualenv = pythonSet.mkVirtualEnv "project-env" workspace.deps.default;

      in {
        devShells.default = pkgs.mkShell {
          packages = [ virtualenv pkgs.uv ];
          shellHook = ''
            echo "⚡ uv2nix environment activated!"
          '';
        };

        packages.default = pkgs.stdenv.mkDerivation {
          pname = "nix-tree";
          version = "0.1.0";
          src = ./.;

          nativeBuildInputs = [ pkgs.makeWrapper ];
          buildInputs = [ virtualenv ];

          installPhase = ''
            mkdir -p $out/bin/
            cp -r * $out/
            
            # Wraps your entry script with the virtual environment's site-packages PATH
            makeWrapper ${virtualenv}/bin/python $out/bin/nix-tree \
              --add-flags "$out/src/nix_tree/__init__.py" \
              --set OPTIONS_LOC $out/data/options.json
          '';
        };
      }
    );
}
