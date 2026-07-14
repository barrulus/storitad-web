{
  description = "Storitad Web — browser capture/browse/edit for the Storitad journal archive";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # inline-snapshot's own test suite is broken in current nixos-unstable
        # (a black-version mismatch in its test_docs.py). It's a check-only
        # dependency of fastapi, so skip its checkPhase to unblock the build.
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (final: prev: {
              pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
                (pyFinal: pyPrev: {
                  inline-snapshot = pyPrev.inline-snapshot.overridePythonAttrs (_: {
                    doCheck = false;
                  });
                })
              ];
            })
          ];
        };
        # Runtime + test Python deps. The package output (buildPythonApplication
        # wrapping whisper-cli + ffmpeg onto PATH) is added in the packaging task.
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          fastapi uvicorn python-multipart jinja2 pyyaml pytest httpx
        ]);
        storitadWeb = pkgs.python312Packages.buildPythonApplication {
          pname = "storitad-web";
          version = "0.1.0";
          pyproject = true;
          src = ./.;
          build-system = [ pkgs.python312Packages.setuptools ];
          dependencies = with pkgs.python312Packages; [
            fastapi uvicorn python-multipart jinja2 pyyaml
          ];
          nativeBuildInputs = [ pkgs.makeWrapper ];
          postFixup = ''
            wrapProgram $out/bin/storitad-web \
              --prefix PATH : ${pkgs.lib.makeBinPath [
                pkgs.whisper-cpp
                pkgs.ffmpeg-headless
              ]}
          '';
          doCheck = false;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.ffmpeg-headless
            pkgs.whisper-cpp
          ];
        };
        packages.default = storitadWeb;
        packages.storitad-web = storitadWeb;
        apps.default = { type = "app"; program = "${storitadWeb}/bin/storitad-web"; };
      });
}
