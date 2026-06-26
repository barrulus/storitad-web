{
  description = "Storitad Web — browser capture/browse/edit for the Storitad journal archive";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # Runtime + test Python deps. The package output (buildPythonApplication
        # wrapping whisper-cli + ffmpeg onto PATH) is added in the packaging task.
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          fastapi uvicorn python-multipart jinja2 pyyaml pytest httpx
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.ffmpeg-headless
            pkgs.whisper-cpp
          ];
        };
      });
}
