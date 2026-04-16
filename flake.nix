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
            # Python
            python
            python.pkgs.pip
            python.pkgs.virtualenv

            # Node.js (frontend)
            pkgs.nodejs_22
            pkgs.nodePackages.npm

            # Native deps required by pip packages
            pkgs.gcc
            pkgs.libffi
            pkgs.openssl
            pkgs.zlib
            pkgs.libjpeg
            pkgs.libxml2
            pkgs.libxslt

            # Runtime tools
            pkgs.ffmpeg
            pkgs.gallery-dl

            # Database / cache clients (for local dev without Docker)
            pkgs.postgresql_14
            pkgs.redis
          ];

          shellHook = ''
            # Activate or create a project-local virtualenv
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
