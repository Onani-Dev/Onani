# NixOS nginx virtual host configuration for Onani.
#
# Import this from your NixOS configuration:
#
#   imports = [ ./path/to/onani/nginx/nixos.nix ];
#
# Then set the options under `services.onani.nginx.*` to match your
# deployment (domain, paths, TLS, etc.).
#
# Prerequisites:
#   - Flask/gunicorn running on `flaskAddress` (default 127.0.0.1:5000)
#   - Vue SPA built to `frontendDistPath`
#   - Static files at `staticPath`, images at `imagesPath`, avatars at `avatarsPath`

{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.services.onani.nginx;
in
{
  options.services.onani.nginx = {
    enable = lib.mkEnableOption "Onani nginx reverse proxy";

    domain = lib.mkOption {
      type = lib.types.str;
      example = "onani.example.com";
      description = "Server name (domain) for the virtual host.";
    };

    flaskAddress = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1:5000";
      description = "Address of the Flask/gunicorn backend.";
    };

    staticPath = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/onani/static";
      description = "Path to the Onani static files directory.";
    };

    imagesPath = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/onani/images";
      description = "Path to uploaded images.";
    };

    avatarsPath = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/onani/avatars";
      description = "Path to user avatars.";
    };

    frontendDistPath = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/onani/frontend/dist";
      description = "Path to the built Vue SPA (output of npm run build).";
    };

    maxUploadSize = lib.mkOption {
      type = lib.types.str;
      default = "200m";
      description = "Maximum upload body size.";
    };

    enableSSL = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Enable ACME/Let's Encrypt TLS via nginx.";
    };
  };

  config = lib.mkIf cfg.enable {
    # Ensure the image_filter module is available
    services.nginx = {
      enable = true;

      additionalModules = [ pkgs.nginxModules.image-filter ];

      recommendedProxySettings = true;
      recommendedTlsSettings = true;
      recommendedGzipSettings = true;
      recommendedOptimisation = true;

      clientMaxBodySize = cfg.maxUploadSize;

      # Security headers applied to all virtual hosts
      appendHttpConfig = ''
        image_filter_buffer 50M;
      '';

      commonHttpConfig = ''
        add_header X-Content-Type-Options  "nosniff" always;
        add_header Referrer-Policy         "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: ws: wss: data: blob: 'unsafe-inline'; frame-ancestors 'self';" always;
        add_header Permissions-Policy      "interest-cohort=()" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
      '';

      virtualHosts.${cfg.domain} = {
        forceSSL = cfg.enableSSL;
        enableACME = cfg.enableSSL;

        locations = {
          # ── Root-level well-known files ─────────────────
          "= /robots.txt" = {
            alias = "${cfg.staticPath}/robots.txt";
            extraConfig = "access_log off;";
          };
          "= /humans.txt" = {
            alias = "${cfg.staticPath}/humans.txt";
            extraConfig = "access_log off;";
          };
          "= /site.webmanifest" = {
            alias = "${cfg.staticPath}/site.webmanifest";
            extraConfig = "access_log off;";
          };
          "= /manifest.json" = {
            alias = "${cfg.staticPath}/manifest.json";
            extraConfig = "access_log off;";
          };
          "= /pwabuilder-sw.js" = {
            alias = "${cfg.staticPath}/pwabuilder-sw.js";
            extraConfig = "access_log off;";
          };

          # ── Static assets ──────────────────────────────
          "/images/" = {
            alias = "${cfg.imagesPath}/";
            extraConfig = "access_log off;";
          };
          "/avatars/" = {
            alias = "${cfg.avatarsPath}/";
            extraConfig = "access_log off;";
          };
          "/static/" = {
            alias = "${cfg.staticPath}/";
            extraConfig = "access_log off;";
          };

          # ── Image thumbnails ───────────────────────────
          "~ ^/(?<route>avatars|images)/thumbnail/(?<name>.*)$" = {
            extraConfig = ''
              access_log off;
              alias ${cfg.imagesPath}/../$route/$name;

              set $size 150;
              if ($arg_size = "xsmall") { set $size 50;  }
              if ($arg_size = "small")  { set $size 150; }
              if ($arg_size = "large")  { set $size 350; }
              if ($arg_size = "xlarge") { set $size 500; }

              image_filter_jpeg_quality 50;
              image_filter resize $size $size;
            '';
          };

          # ── Sample (preview) images ────────────────────
          "~ ^/sample/(?<name>.*)$" = {
            extraConfig = ''
              access_log off;
              alias ${cfg.imagesPath}/$name;
              image_filter_jpeg_quality 80;
              image_filter resize 800 2000;
            '';
          };

          # ── Vue SPA (hashed assets) ────────────────────
          "/assets/" = {
            alias = "${cfg.frontendDistPath}/assets/";
            extraConfig = ''
              access_log off;
              expires 30d;
            '';
          };

          # ── Flask backend (API, admin, feeds) ──────────
          "/api/" = {
            proxyPass = "http://${cfg.flaskAddress}";
          };
          "/admin/" = {
            proxyPass = "http://${cfg.flaskAddress}";
          };
          "/atom/" = {
            proxyPass = "http://${cfg.flaskAddress}";
          };
          "/rss/" = {
            proxyPass = "http://${cfg.flaskAddress}";
          };

          # ── SPA catch-all (must be last) ────────────────
          "/" = {
            root = cfg.frontendDistPath;
            tryFiles = "$uri $uri/ /index.html";
          };
        };
      };
    };
  };
}
