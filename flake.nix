{
  description = "Onani development environment";

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
        python = pkgs.python313;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            python.pkgs.pip
            python.pkgs.virtualenv
            pkgs.nodejs_22
            pkgs.gcc
            pkgs.libffi
            pkgs.openssl
            pkgs.zlib
            pkgs.libjpeg
            pkgs.libxml2
            pkgs.libxslt
            pkgs.ffmpeg
            pkgs.gallery-dl
            pkgs.postgresql_14
            pkgs.redis
          ];

          shellHook = ''
            if [ ! -d .venv ]; then
              echo "Creating virtualenv in .venv ..."
              ${python}/bin/python -m venv .venv
            fi
            source .venv/bin/activate

            export FLASK_APP=run
            export FLASK_ENV=development
          '';

          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.libffi
            pkgs.openssl
            pkgs.zlib
            pkgs.libjpeg
            pkgs.libxml2
            pkgs.libxslt
            pkgs.stdenv.cc.cc.lib
          ];
        };
      }
    );
}
