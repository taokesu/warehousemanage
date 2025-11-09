{ pkgs, ... }: {
  channel = "stable-24.05";
  packages = [ pkgs.python3 ];
  env = {};
  idx.previews = {
    enable = true;
    previews = {
      web = {
        command = [ "./devserver.sh" ];
        manager = "web";
      };
    };
  };
}