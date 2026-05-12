# MCSM - Minecraft Server Management

A tool for managing servers, installing the jars, updating mods, maybe more.

## Installation
It will be put up on PYPI, but for now a manual install from this repo is required.

#### Requirements
- uv - https://github.com/astral-sh/uv
```
git clone https://github.com/Johnny-Airlines/MCSM.git
cd MCSM
uv tool install .
cd ..
rm -rf ./MCSM
```

## Usage
Will be updated. For now please just use the help provided with --help, the command is mcsm. For help on a subcommand, run mcsm [subcommand] --help.

## Uninstallation
```
uv tool uninstall minecraft-server-management
