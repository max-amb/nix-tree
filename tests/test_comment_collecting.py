from pathlib import Path
import pytest

from nix_tree.decomposer import CommentHandling

def test_shortened_default():
    """
    Checks if all of the comments are collected in the right way from the shortened_default.nix configuration
    """

    comment_handler = CommentHandling(Path("./tests/example_configurations/shortened_default.nix"))
    assert "{3: [('# Edit this configuration file to define what should be installed on', True), ('# your system.  Help is available in the configuration.nix(5) man page', True), ('# and in the NixOS manual (accessible by running ‘nixos-help’).', True)], 12: [('# Define your hostname.\\n', False)], 14: [('# networking.wireless.enable = true;  # Enables wireless support via wpa_supplicant.', True)], 18: [('# Configure network proxy if necessary', True), ('# networking.proxy.default = \"http://user:password@proxy:port/\";', True), ('# networking.proxy.noProxy = \"127.0.0.1,localhost,internal.domain\";', True)], 20: [('# Enable networking', True)], 23: [('# Set your time zone.', True)], 26: [('# Select internationalisation properties.', True)], 29: [('# Enable the X11 windowing system.', True)], 33: [('# Enable touchpad support (enabled default in most desktopManager).', True), ('# services.xserver.libinput.enable = true;', True)], 35: [('# Install firefox.', True)], 38: [('# Allow unfree packages', True)], 42: [('# List packages installed in system profile. To search, run:', True), ('# $ nix search wget', True)], 49: [('# Open ports in the firewall.', True), ('# networking.firewall.allowedTCPPorts = [ ... ];', True), ('# networking.firewall.allowedUDPPorts = [ ... ];', True), ('# Or disable the firewall altogether.', True), ('# networking.firewall.enable = false;', True)], 56: [('# This value determines the NixOS release from which the default', True), ('# settings for stateful data, like file locations and database versions', True), ('# on your system were taken. It‘s perfectly fine and recommended to leave', True), ('# this value at the release version of the first install of this system.', True), ('# Before changing this value read the documentation for this option', True), ('# (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).', True), ('# Did you read the comment?\\n', False)]}".replace("\"", '"') == str(comment_handler.get_comments_for_attaching())


