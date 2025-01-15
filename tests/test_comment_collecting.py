"""Tests the comment collecting functions for accuracy"""
from pathlib import Path

from nix_tree.decomposer import CommentHandling

def test_shortened_default():
    """
    Checks if all of the comments are collected in the right way from the shortened_default.nix configuration
    """

    comment_handler = CommentHandling(Path("./tests/example_configurations/shortened_default.nix"))
    assert "{5: [(\'# Edit this configuration file to define what should be installed on\', True), (\'# your system.  Help is available in the configuration.nix(5) man page\', True), (\'# and in the NixOS manual (accessible by running ‘nixos-help’).\', True)], 14: [(\'# Define your hostname.\\n\', False)], 16: [(\'# networking.wireless.enable = true;  # Enables wireless support via wpa_supplicant.\', True)], 20: [(\'# Configure network proxy if necessary\', True), (\'# networking.proxy.default = \"http://user:password@proxy:port/\";\', True), (\'# networking.proxy.noProxy = \"127.0.0.1,localhost,internal.domain\";\', True)], 22: [(\'# Enable networking\', True)], 25: [(\'# Set your time zone.\', True)], 28: [(\'# Select internationalisation properties.\', True)], 31: [(\'# Enable the X11 windowing system.\', True)], 35: [(\'# Enable touchpad support (enabled default in most desktopManager).\', True), (\'# services.xserver.libinput.enable = true;\', True)], 37: [(\'# Install firefox.\', True)], 40: [(\'# Allow unfree packages\', True)], 44: [(\'# List packages installed in system profile. To search, run:\', True), (\'# $ nix search wget\', True)], 51: [(\'# Open ports in the firewall.\', True), (\'# networking.firewall.allowedTCPPorts = [ ... ];\', True), (\'# networking.firewall.allowedUDPPorts = [ ... ];\', True), (\'# Or disable the firewall altogether.\', True), (\'# networking.firewall.enable = false;\', True)], 58: [(\'# This value determines the NixOS release from which the default\', True), (\'# settings for stateful data, like file locations and database versions\', True), (\'# on your system were taken. It‘s perfectly fine and recommended to leave\', True), (\'# this value at the release version of the first install of this system.\', True), (\'# Before changing this value read the documentation for this option\', True), (\'# (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).\', True), (\'# Did you read the comment?\\n\', False)]}".replace("\"", '"') == str(comment_handler.get_comments_for_attaching())

def test_yasu_example_config():
    """
    Checks if all comments are collected correctly in yasu_example_config.nix configuration
    """

    comment_handler = CommentHandling(Path("./tests/example_configurations/yasu_example_config.nix"))
    assert "{6: [('# Include the results of the hardware scan.\\n', False)], 13: [('# Define your hostname.\\n', False)], 23: [('#audio', True)], 38: [('# Steam\\n', False)]}".replace("\"", '"') == str(comment_handler.get_comments_for_attaching())

def test_pms_example_config():
    """
    Checks if all comments are collected correctly in pms_example_config.nix configuration
    """

    comment_handler = CommentHandling(Path("./tests/example_configurations/pms_example_config.nix"))
    assert "{6: [('# Edit this configuration file to define what should be installed on', True), ('# your system.  Help is available in the configuration.nix(5) man page', True), ('# and in the NixOS manual (accessible by running `nixos-help`).', True)], 11: [('# Include the results of the hardware scan.\\n', False)], 16: [('# Use the systemd-boot EFI boot loader.', True)], 22: [('#boot.zfs.extraPools = [ \"zfstest\" ];', True)], 57: [('# badblocks\\n', False)], 97: [('#defaultSession = \"xfce+bspwm\";', True)], 110: [('# make shares visible for windows 10 clients\\n', False)]}".replace("\"", '"') == str(comment_handler.get_comments_for_attaching())

def test_random():
    """
    Checks if all comments are collected correctly in random.nix configuration
    """

    comment_handler = CommentHandling(Path("./tests/example_configurations/random.nix"))
    assert "{3: [('# To test multiline headers', True)], 9: [('# from hardware_configuration.nix bundled in a install of Nix-OS', True)], 12: [('# networking.interfaces.ens33.useDHCP = lib.mkDefault true;', True)], 16: [('# To test lib.mkForce, taken from https://search.nixos.org/options?channel=24.11&show=boot.supportedFilesystems&from=0&size=50&sort=relevance&type=packages&query=lib.mkForce', True)], 23: [('# Testing integers', True)]}".replace("\"", '"') == str(comment_handler.get_comments_for_attaching())
