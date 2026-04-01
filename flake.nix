{
  description = "hello world application using uv2nix";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

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

  outputs =
    {
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      # Per-system configuration
      perSystem =
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python314;

          pythonSet =
            (pkgs.callPackage pyproject-nix.build.packages {
              inherit python;
            }).overrideScope
              (
                lib.composeManyExtensions [
                  pyproject-build-systems.overlays.wheel
                  overlay
                ]
              );

          editablePythonSet = pythonSet.overrideScope editableOverlay;
          python3Packages = pkgs.python314Packages;
        in
        {
          devShell = pkgs.mkShell {
            packages = [
              (editablePythonSet.mkVirtualEnv "hello-world-dev-env" workspace.deps.all)
              pkgs.uv
              pkgs.nodePackages.prettier
              pkgs.neovim
              pkgs.basedpyright
              pkgs.htmx-lsp
              pkgs.ruff
              python3Packages.python-lsp-server
              python3Packages.pylsp-rope
              python3Packages.debugpy
            ];
            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = pythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };
            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
            '';
          };

          package = pythonSet.mkVirtualEnv "hello-world-env" workspace.deps.default;
        };

    in
    {
      devShells = forAllSystems (system: {
        default = (perSystem system).devShell;
      });

      packages = forAllSystems (system: {
        default = (perSystem system).package;
      });
    };
}
