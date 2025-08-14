{
  description = "Workshop watcher Python dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        # Pick desired Python version
        python = pkgs.python312;
        # Declare Python packages needed by the script
        pythonEnv = python.withPackages (
          ps: with ps; [
            # Add/adjust dependencies below
            requests
            # watchdog
            # pyyaml
            # click
          ]
        );
        scriptName = "workshop-watcher"; # final executable name
        src = ./.; # project root
        # Determine how to install (single file vs package dir)
        installScript =
          if builtins.pathExists ./workshop_watcher/__init__.py then
            ''
              mkdir -p $out/bin
              cat > $out/bin/${scriptName} <<'EOF'
              #!${pythonEnv}/bin/python
              from workshop_watcher.__main__ import main
              if __name__ == "__main__":
                  main()
              EOF
              chmod +x $out/bin/${scriptName}
            ''
          else if builtins.pathExists ./workshop_watcher.py then
            ''
              install -Dm755 workshop_watcher.py $out/bin/${scriptName}
            ''
          else
            ''
              echo "No workshop_watcher.py or package directory found" >&2
              exit 1
            '';
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = scriptName;
          version = "0.1.0";
          inherit src;
          buildInputs = [ pythonEnv ];
          dontBuild = true;
          installPhase = ''
            runHook preInstall
            ${installScript}
            runHook postInstall
          '';
        };

        # nix develop
        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.ruff
            pkgs.git
            pkgs.just
            pkgs.sqlite
          ];
          shellHook = ''
            echo "Entering ${scriptName} dev shell (Python ${python.version})"
            echo "Add dependencies by editing flake.nix python.withPackages list."
          '';
        };

        # nix run
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/${scriptName}";
        };
      }
    );
}
