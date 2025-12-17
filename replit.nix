{pkgs}: {
  deps = [
    pkgs.python313Packages.sqlalchemy_1_4
    pkgs.python312Packages.flask
    pkgs.yt-dlp
    pkgs.postgresql
    pkgs.openssl
  ];
}
