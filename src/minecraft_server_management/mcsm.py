import os
import requests
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
    ctx.command.params[2].type = click.Choice(versionIds)
    ctx.command.params[2].choices = versionIds
    ctx.command.params[2].required = True


def version_defined(ctx, param, value):
    if not param.required:
        click.echo("Please specify mod loader before specifying version.")
        quit()


@mcsm.command("setup")
@click.option(
    "--override",
    "-o",
    "override",
    help="Enables overriding pre-existing configurations.",
    is_flag=True,
)
@choice_option(
    "--mod-loader",
    "-ml",
    help="The mod loader to use.",
    type=click.Choice(["Vanilla", "Fabric"]),
    callback=get_version,
)
@auto_complete_option(
    "--version", "-v", help="The version.", required=False, callback=version_defined
)
def setup(override, mod_loader, version):
    if os.path.exists("./conf.json"):
        if not override:
            override = click.confirm(
                "Conf.json already found, override?", default=False
            )
        if not override:
            return
    click.echo("Setup")


@mcsm.command("remove")
def remove():
    click.echo("Removing")
