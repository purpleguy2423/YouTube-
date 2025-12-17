{pkgs}: {
  deps = [
    pkgs.python312Packages.flask
    pkgs.yt-dlp
    pkgs.postgresql
    pkgs.openssl
  ];
}
