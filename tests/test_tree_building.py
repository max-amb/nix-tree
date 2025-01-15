"""Tests the tree building functions"""

from pathlib import Path

from nix_tree.tree import DecomposerTree, ConnectorNode, VariableNode, Node
from nix_tree.decomposer import Decomposer

YASU_TREE = """
  |--headers=[ config, pkgs, ... ]
  |--imports=[ ./hardware-configuration.nix ]
  boot
    loader
      systemd-boot
        |--enable=true
      efi
        |--canTouchEfiVariables=true
  networking
    |--hostName='nixos'
    |--defaultGateway='10.11.12.1'
    |--nameservers=[ '10.11.12.1' ]
    firewall
      |--allowedTCPPorts=[ 3389 ]
  time
    |--timeZone='Japan'
  virtualisation
    virtualbox
      host
        |--enable=true
  hardware
    bluetooth
      |--enable=true
      config
        General
          |--Enable='Source,Sink,Media,Socket'
    pulseaudio
      |--enable=true
      |--extraModules=[ pkgs.pulseaudio-modules-bt ]
      |--package=pkgs.pulseaudioFull
      |--support32Bit=true
      |--extraConfig='' load-module module-bluetooth-policy auto_switch = 2 ''
    opengl
      |--driSupport32Bit=true
  services
    blueman
      |--enable=true
    cron
      |--enable=true
      |--systemCronJobs=[ '@reboot root ${pkgs.ethtool}/sbin/ethtool -s enp4s0 wol g' ]
    openssh
      |--enable=true
      |--passwordAuthentication=false
      |--challengeResponseAuthentication=false
      |--extraConfig='UseDNS yes'
    vsftpd
      |--enable=true
      |--localUsers=true
      |--writeEnable=true
      |--extraConfig='' pasv_enable = YES connect_from_port_20 = YES pasv_min_port = 4242 pasv_max_port = 4243 ''
    apcupsd
      |--enable=true
      |--configText=''  UPSCABLE smart UPSTYPE apcsmart DEVICE /dev/ttyS0 ''
    postfix
      |--enable=true
      |--setSendmail=true
    xserver
      |--enable=true
      |--layout='us'
      displayManager
        gdm
          |--enable=true
      desktopManager
        gnome3
          |--enable=true
      |--videoDrivers=[ 'nvidia' ]
    fail2ban
      |--enable=true
    netdata
      |--enable=true
    xrdp
      |--enable=true
      |--defaultWindowManager='${pkgs.icewm}/bin/icewm'
    vnstat
      |--enable=true
  sound
    |--enable=true
  programs
    mosh
      |--enable=true
    gnupg
      agent
        |--enable=true
  systemd
    targets
      sleep
        |--enable=false
      suspend
        |--enable=false
      hibernate
        |--enable=false
      hybrid-sleep
        |--enable=false
  users
    extraUsers
      yasu
        |--home='/home/yasu'
        |--isNormalUser=true
        |--uid=1000
        |--extraGroups=[ 'wheel' ]
  nixpkgs
    config
      |--allowUnfree=true
  powerManagement
    |--enable=true
  i18n
    inputMethod
      |--enabled='ibus'
      ibus
        |--engines=[ (pkgs.ibus-engines).mozc ]
  fonts
    |--fonts=[ (pkgs).carlito (pkgs).dejavu_fonts (pkgs).ipafont (pkgs).kochi-substitute (pkgs).source-code-pro (pkgs).ttf_bitstream_vera ]
    fontconfig
      defaultFonts
        |--monospace=[ 'DejaVu Sans Mono' 'IPAGothic' ]
        |--sansSerif=[ 'DejaVu Sans' 'IPAPGothic' ]
        |--serif=[ 'DejaVu Serif' 'IPAPMincho' ]
"""

SHORTENED_DEFAULT_TREE = """
  |--headers=[ config, pkgs, ... ]
  |--imports=[ ./hardware-configuration.nix ]
  boot
    loader
      grub
        |--enable=true
        |--device='/dev/sda'
        |--useOSProber=true
  networking
    |--hostName='nixos'
    networkmanager
      |--enable=true
  time
    |--timeZone='Europe/London'
  i18n
    |--defaultLocale='en_GB.UTF-8'
  services
    xserver
      |--enable=true
  programs
    firefox
      |--enable=true
  nixpkgs
    config
      |--allowUnfree=true
  environment
    |--systemPackages=[ (pkgs).vim (pkgs).git ]
  system
    |--stateVersion='23.11'
"""

PMS_TREE = """
  |--headers=[ config, pkgs, ... ]
  |--imports=[ ./hardware-configuration.nix ]
  boot
    loader
      systemd-boot
        |--enable=true
      efi
        |--canTouchEfiVariables=true
    |--supportedFilesystems=[ 'zfs' ]
    zfs
      |--forceImportRoot=false
  services
    zfs
      autoScrub
        |--enable=true
    openssh
      |--enable=true
      settings
        |--PasswordAuthentication=false
        |--PermitRootLogin='yes'
    tailscale
      |--enable=true
    xserver
      |--enable=true
      displayManager
        lightdm
          |--enable=true
        |--defaultSession='xfce'
      desktopManager
        xfce
          |--enable=true
      windowManager
        bspwm
          |--enable=true
    samba-wsdd
      |--enable=true
    samba
      |--enable=true
      |--securityType='user'
      |--extraConfig='' workgroup = KTZ server string = testnix netbios name = testnix security = user guest ok = yes guest account = nobody map to guest = bad user load printers = no ''
      shares
        zfstest
          |--path='/mnt/zfstest'
          |--browseable='yes'
          |--'read only'='no'
          |--'guest ok'='yes'
          |--'create mask'='0644'
          |--'directory mask'='0755'
          |--'force user'='alex'
          |--'force group'='users'
  time
    |--timeZone='America/New_York'
  users
    users
      alex
        |--isNormalUser=true
        |--extraGroups=[ 'wheel' 'docker' ]
        openssh
          authorizedKeys
            |--keyFiles=[ /etc/nixos/ssh/authorized_keys ]
      users
        root
          openssh
            authorizedKeys
              |--keyFiles=[ /etc/nixos/ssh/authorized_keys ]
  environment
    |--systemPackages=[ (pkgs).docker-compose (pkgs).htop (pkgs).hddtemp (pkgs).intel-gpu-tools (pkgs).iotop (pkgs).lm_sensors (pkgs).mergerfs (pkgs).mc (pkgs).ncdu (pkgs).nmap (pkgs).nvme-cli (pkgs).sanoid (pkgs).snapraid (pkgs).tdns-cli (pkgs).tmux (pkgs).tree (pkgs).vim (pkgs).wget (pkgs).smartmontools (pkgs).e2fsprogs ]
  networking
    firewall
      |--enable=false
    |--hostName='testnix'
    |--hostId='e5f2dc02'
    interfaces
      enp1s0
        |--useDHCP=false
    |--defaultGateway='10.42.0.254'
    |--nameservers=[ '10.42.0.253' ]
  virtualisation
    docker
      |--enable=true
      autoPrune
        |--enable=true
        |--dates='weekly'
  nix
    settings
      |--experimental-features=[ 'nix-command' 'flakes' ]
      |--warn-dirty=false
  system
    |--copySystemConfiguration=true
    |--stateVersion='23.05'
"""

RANDOM = """
  |--headers=[ lib, ... ]
  networking
    |--useDHCP=lib.mkDefault.true
  nixpkgs
    |--hostPlatform=lib.mkDefault.'x86_64-linux'
  boot
    supportedFilesystems
      |--btrfs=true
      |--zfs=lib.mkForce.false
  services
    i2pd
      |--bandwidth=32
    tigerbeetle
      |--clusterId=15
"""

def tree_output(node: Node, append: str = "", output_string: str = "") -> str:
    """
    Outputs the tree in an easier format for testing - its a really similar function to tree.quick_display()

    Args:
        node: Node - the node to start displaying the tree from
        append: str - to store position in the tree
        output_string: str - the string each frame of the function is adding to to be finally ouputted

    Returns:
        str: The tree outputted in string form
    """

    if isinstance(node, ConnectorNode):
        output_string += append + node.get_name() + "\n"
        for i in node.get_connected_nodes():
            output_string = tree_output(i, append + "  ", output_string)
    if isinstance(node, VariableNode):
        output_string += append + "|--" + node.get_name().split(".")[-1] + "=" + node.get_data() + "\n"
    return output_string

def test_tree_for_yasu_example_config():
    """
    Checks if the tree generator functions in decomposer and tree work as expected for the yasu example config
    """

    tree = DecomposerTree()
    Decomposer(file_path=Path("./tests/example_configurations/yasu_example_config.nix"), tree=tree)
    assert YASU_TREE == tree_output(tree.get_root())


def test_tree_for_shortened_default_config():
    """
    Checks if the tree generator functions in decomposer and tree work as expected for the shortened default config
    """

    tree = DecomposerTree()
    Decomposer(file_path=Path("./tests/example_configurations/shortened_default.nix"), tree=tree)
    assert SHORTENED_DEFAULT_TREE == tree_output(tree.get_root())

def test_tree_for_pms_example_config():
    """
    Checks if the tree generator functions in decomposer and tree work as expected for the pms example config
    """

    tree = DecomposerTree()
    Decomposer(file_path=Path("./tests/example_configurations/pms_example_config.nix"), tree=tree)
    assert PMS_TREE == tree_output(tree.get_root())

def test_tree_for_random():
    """
    Checks if the tree generator functions in decomposer and tree work as expected for the random config
    """

    tree = DecomposerTree()
    Decomposer(file_path=Path("./tests/example_configurations/random.nix"), tree=tree)
    assert RANDOM == tree_output(tree.get_root())
