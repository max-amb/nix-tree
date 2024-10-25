{ config, pkgs, ... }:
{
  imports =
    [ # Include the results of the hardware scan.
      ./hardware-configuration.nix
    ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = 
  true;
  networking.hostName = "nixos"; # Define your hostname.
  networking.defaultGateway = "10.11.12.1";
  networking.nameservers = [ "10.11.12.1" ];

  time.timeZone = "Japan";

  virtualisation.virtualbox.host.enable = true;

  
  #audio
  hardware.bluetooth = {
    enable = true;
    config = {
      General = {
        Enable = "Source,Sink,Media,Socket";
      };
    };
  };
  services.blueman.enable = true;

  sound.enable = true;
  hardware.pulseaudio = {
    enable = true;
    extraModules = [ pkgs.pulseaudio-modules-bt ];
    package = pkgs.pulseaudioFull;
    support32Bit = true; # Steam
    extraConfig = ''
      load-module module-bluetooth-policy auto_switch=2
    '';
  };

  services.cron.enable = true;
  services.cron.systemCronJobs = ["@reboot root ${pkgs.ethtool}/sbin/ethtool -s enp4s0 wol g"];


  services.openssh.enable = true;
  services.openssh.passwordAuthentication = false;
  services.openssh.challengeResponseAuthentication= false;
  services.openssh.extraConfig = "UseDNS yes";
  programs.mosh.enable = true;


  systemd.targets.sleep.enable = false;
  systemd.targets.suspend.enable = false;
  systemd.targets.hibernate.enable = false;
  systemd.targets.hybrid-sleep.enable = false;


  services.vsftpd.enable = true;
  services.vsftpd.localUsers = true;
  services.vsftpd.writeEnable= true;
  services.vsftpd.extraConfig = ''
				pasv_enable=YES
				connect_from_port_20=YES
				pasv_min_port=4242
				pasv_max_port=4243
				'';

  services.apcupsd.enable=true;
  services.apcupsd.configText= '' 
           UPSCABLE smart
           UPSTYPE  apcsmart
           DEVICE   /dev/ttyS0
       '';

  services.postfix = {
    enable = true;
    setSendmail = true;
  };

  services.xserver.enable = true;
  services.xserver.layout = "us";

  services.xserver.displayManager.gdm.enable = true;
  services.xserver.desktopManager.gnome3.enable = true;

   users.extraUsers.yasu = {
     home="/home/yasu";
     isNormalUser = true;
     uid = 1000;
     extraGroups = ["wheel" ];

   };

  nixpkgs.config.allowUnfree = true;
  services.xserver.videoDrivers = [ "nvidia" ];
  powerManagement.enable = true; 
  hardware.opengl.driSupport32Bit = true;
  services.fail2ban.enable = true;

  services.netdata.enable = true;

  programs.gnupg.agent.enable = true;
  services.xrdp.enable = true;
  networking.firewall.allowedTCPPorts = [ 3389 ];
  services.xrdp.defaultWindowManager = "${pkgs.icewm}/bin/icewm";

  services.vnstat.enable = true;
  i18n.inputMethod = {
    enabled = "ibus";
    ibus.engines = with pkgs.ibus-engines; [ /* any engine you want, for example */ mozc ];
  };

  fonts.fonts = with pkgs; [
    carlito
    dejavu_fonts
    ipafont
    kochi-substitute
    source-code-pro
    ttf_bitstream_vera
  ];

  fonts.fontconfig.defaultFonts = {
    monospace = [
      "DejaVu Sans Mono"
      "IPAGothic"
    ];
    sansSerif = [
      "DejaVu Sans"
      "IPAPGothic"
    ];
    serif = [
      "DejaVu Serif"
      "IPAPMincho"
    ];
  };
}
