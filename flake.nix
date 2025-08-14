{
  description = "Workshop watcher Python script";

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
        python = pkgs.python312; # stdlib only now
        scriptName = "workshop-watcher";
        src = ./.;
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = scriptName;
          version = "0.1.0";
          inherit src;
          dontBuild = true;
          installPhase = ''
            runHook preInstall
            mkdir -p $out/bin
            mkdir -p $out/lib/${scriptName}
            cp *.py $out/lib/${scriptName}/
            cat > $out/bin/${scriptName} <<'EOF'
            #!/usr/bin/env bash
            export PYTHONPATH="$out/lib/${scriptName}:$PYTHONPATH"
            exec ${python}/bin/python $out/lib/${scriptName}/main.py "$@"
            EOF
            chmod +x $out/bin/${scriptName}
            runHook postInstall
          '';
        };

        devShells.default = pkgs.mkShell {
          packages = [
            python
            pkgs.ruff
            pkgs.sqlite
          ];
          shellHook = ''
            echo "Dev shell for ${scriptName} (Python ${python.version})"
            echo "Run: python main.py --help"
          '';
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/${scriptName}";
        };
      }
    );
}
