# Nix-tree
A tool for viewing and editing your nix configuration as a tree

## RUN 🏃
* Note this tool currently is only tested for NixOS, so if you aren't on NixOS use it at your peril!

#### Enabling flakes ❄️
* To run this program you will need nix flakes enabled (or you can append the option for every command)
* So to enable nix flakes for just your user add this to your home-manager configuration:
```nix
nix = {
    package = pkgs.nix;
    settings.experimental-features = [ "nix-command" "flakes" ];
};
```
* Or to enable it system wide:
```nix
nix.settings.experimental-features = [ "nix-command" "flakes" ];
```
* Finally, if you just want to enable it on a command-by-command basis append `--experimental-features 'nix-command flakes'` to every command

#### Building and running the program 👷
* The program is wrapped in a flake, so it can be run with:
```nix
nix run 'github:max-amb/nix-tree' <your filename>
```
* There are two options which you can enable when running the program
    * `-w` which will enable writing over of the original file
    * `-c` which will enable comments being copied over


## COMING UP⏭️
- [ ] More safety rails for the user, e.g. more pattern matching in inputs
- [ ] Complete support of the basic Nix language
- [ ] The ability to analyse flakes (e.g.`in`statements)

