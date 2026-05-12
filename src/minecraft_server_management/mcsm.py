import os
import requests
import json
import click
from click_prompt import choice_option, auto_complete_option


@click.group()
def mcsm():
    click.echo("Minecraft Server Management")


def get_version(ctx, param, value):
    if value == "Vanilla":
        r = requests.get(
            "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        )
        version_manifest = r.json()
        versions = version_manifest["versions"]
        versionIds = [v["id"] for v in versions]

    if value == "Fabric":
        r = requests.get("https://meta.fabricmc.net/v2/versions/game")
        response = r.json()
        versionIds = [v["version"] for v in response]
    ctx.command.params[3].type = click.Choice(versionIds)
    ctx.command.params[3].choices = versionIds
    ctx.command.params[3].required = True
    return value


def version_defined(ctx, param, value):
    if not param.required:
        click.echo("Please specify mod loader before specifying version.")
        quit()
    return value


@mcsm.command("setup")
@click.option(
    "--dir",
    "-d",
    "dir",
    default="./",
    help="Filepath to server directory. Must exist beforehand. Default is current directory.",
    type=click.Path(exists=True),
)
@click.option(
    "--override",
    "-o",
    help="Enables overriding pre-existing configurations.",
    is_flag=True,
)
@choice_option(
    "-ml",
    "--mod-loader",
    help="The mod loader to use.",
    type=click.Choice(["Vanilla", "Fabric"]),
    callback=get_version,
)
@auto_complete_option(
    "--version", "-v", help="The version.", required=False, callback=version_defined
)
def setup(dir, override, mod_loader, version):
    print(mod_loader)
    path_to_conf = os.path.join(dir, "conf.json")
    if os.path.exists(path_to_conf):
        if not override:
            override = click.confirm(
                "Conf.json already found, override?", default=False
            )
        if not override:
            return
    click.echo("Creating conf.json")
    with open(path_to_conf, "w") as conf:
        json.dump({"mod-loader": mod_loader, "version": version}, conf, indent=4)


@mcsm.command("remove")
def remove():
    click.echo("Removing")
