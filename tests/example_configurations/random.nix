/* This file contains random elements from different nix configurations and my own hand to ensure all elements of the program are sufficiently covered in unit tests */

# To test multiline headers
{ lib,
...
}:

{
  # from hardware_configuration.nix bundled in a install of Nix-OS

  networking.useDHCP = lib.mkDefault true;
  # networking.interfaces.ens33.useDHCP = lib.mkDefault true;

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";

  # To test lib.mkForce, taken from https://search.nixos.org/options?channel=24.11&show=boot.supportedFilesystems&from=0&size=50&sort=relevance&type=packages&query=lib.mkForce

  boot.supportedFilesystems = {
    btrfs = true;
    zfs = lib.mkForce false;
  };

  # Testing integers

  services.i2pd.bandwidth = 32;
  services.tigerbeetle.clusterId = 15;

}

