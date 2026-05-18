import os
import subprocess
from time import sleep, time
import requests
import json
import click
from click_prompt import choice_option, auto_complete_option
import questionary
import rich.progress
from term_image.image import from_url


def download_file(url, path, message):
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get("content-length", 0))
    decorations = [
        rich.progress.BarColumn(),
        rich.progress.DownloadColumn(),
        rich.progress.TransferSpeedColumn(),
        rich.progress.TimeRemainingColumn(),
    ]
    with rich.progress.Progress(f"[bold cyan]{message}[/]", *decorations) as progress:
        task = progress.add_task("download_file", total=total_size)
        with open(path, mode="wb") as file:
            for chunk in r.iter_content(chunk_size=1024):
                progress.update(task, advance=len(chunk))
                file.write(chunk)


@click.group()
def mcsm():
    click.echo("Minecraft Server Management")


def get_version(ctx, param, value):
    if value == "vanilla":
        r = requests.get(
            "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        )
        version_manifest = r.json()
        versions = version_manifest["versions"]
        version_ids = [v["id"] for v in versions]

    if value == "fabric":
        r = requests.get("https://meta.fabricmc.net/v2/versions/game")
        response = r.json()
        version_ids = [v["version"] for v in response]
    ctx.command.params[3].type = click.Choice(version_ids)
    ctx.command.params[3].choices = version_ids
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
    type=click.Choice(["vanilla", "fabric"]),
    callback=get_version,
)
@auto_complete_option(
    "--version", "-v", help="The version.", required=False, callback=version_defined
)
def setup(dir, override, mod_loader, version):
    global version_ids_urls
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
        json.dump(
            {"mod_loader": mod_loader, "version": version, "uid": time(), "mods": []},
            conf,
            indent=4,
        )
    os.makedirs(os.path.join(dir, "mods"))
    if mod_loader == "vanilla":
        r = requests.get(
            "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        )
        version_manifest = r.json()
        versions = version_manifest["versions"]
        for version_info in versions:
            if version_info["id"] == version:
                version_json_url = version_info["url"]
                break
        r = requests.get(version_json_url)
        version_url = r.json()["downloads"]["server"]["url"]
    elif mod_loader == "fabric":
        version_url = f"https://meta.fabricmc.net/v2/versions/loader/{version}/0.19.2/1.1.1/server/jar"
    download_file(
        version_url, os.path.join(dir, "server.jar"), "Downloading server jar"
    )


@mcsm.command("start")
@click.option(
    "--dir",
    "-d",
    "dir",
    default="./",
    help="Filepath to server directory. Must exist. Default is current directory.",
    type=click.Path(exists=True),
)
@click.option("--detach", help="Never attaches, just starts.", is_flag=True)
def start(dir, detach):
    path_to_conf = os.path.join(dir, "conf.json")
    if not os.path.exists(path_to_conf):
        raise click.ClickException("Not a mcsm managed server. No conf.json found.")
    with open(path_to_conf) as conf:
        uid = json.load(conf)["uid"]

    click.echo("Starting server and entering the server console.")
    click.echo("To detach, press ctrl-a then d.")
    click.echo("Starting ...")
    sleep(5)
    subprocess.run(f"screen -S {uid} -d -m", shell=True)
    subprocess.run(f"screen -r {uid} -X stuff $'cd {dir}\n'", shell=True)
    subprocess.run(
        f"screen -r {uid} -X stuff $'echo eula=true > eula.txt\n'", shell=True
    )
    subprocess.run(
        f"screen -r {uid} -X stuff $'java -jar server.jar nogui\n'", shell=True
    )
    subprocess.run(f"screen -r {uid}", shell=True)


@mcsm.command("console")
@click.option(
    "--dir",
    "-d",
    "dir",
    default="./",
    help="Filepath to server directory. Must exist. Default is current directory.",
    type=click.Path(exists=True),
)
def console(dir):
    path_to_conf = os.path.join(dir, "conf.json")
    if not os.path.exists(path_to_conf):
        raise click.ClickException("Not a mcsm managed server. No conf.json found.")
    with open(path_to_confClickException) as conf:
        uid = json.load(conf)["uid"]
    click.echo("Entering the server cmd line/logs.")
    click.echo("To detach, press ctrl-a then d.")
    click.echo("Entering ...")
    sleep(5)
    subprocess.run(f"screen -R {uid}", shell=True)


@mcsm.command("remove")
def remove():
    click.echo("Removing")


@mcsm.group()
def mods():
    pass


@mods.command("install")
@click.option(
    "--dir",
    "-d",
    "dir",
    default="./",
    help="Filepath to server directory. Must exist. Default is current directory.",
    type=click.Path(exists=True),
)
@click.option("--query", "-q", help="The query string for the mod.")
@click.option("--project-id", "-id", help="The project id of the mod.")
def install(dir, query, project_id):
    path_to_conf = os.path.join(dir, "conf.json")
    if not os.path.exists(path_to_conf):
        raise click.ClickException("Not a mcsm managed server. No conf.json found.")
    with open(path_to_conf) as conf:
        data = json.load(conf)
        version = data["version"]
        mod_loader = data["mod_loader"]
        mods = data["mods"]
    if query == None:
        if project_id == None:
            raise click.ClickException(
                "Please specify either a query and interactively select a mod, or give a project id."
            )
        click.echo(project_id)
        return
    r = requests.get(
        "https://api.modrinth.com/v2/search",
        params={
            "query": query,
            "facets": f'[["categories:{mod_loader}"],["versions:{version}"],["project_type:mod"]]',
        },
    )
    results = r.json()
    if results["total_hits"] == 0:
        click.echo("No search results.")
        return
    for hit in results["hits"][:3]:
        icon_url = hit["icon_url"]
        if hit["icon_url"] == "":
            icon_url = "https://modrinth.com/favicon.ico"
        image = from_url(icon_url, width=15)
        image = "{:1.1}".format(image)
        image_lines = str(image).splitlines()
        click.secho(f"{image_lines[0]}    {hit['title']}", bold=True)
        image_lines.pop(0)
        clean_description = hit["description"].replace("\n", " ")
        click.echo(f"{image_lines[0]}    {clean_description}")
        image_lines.pop(0)
        print("\n".join(image_lines))
    choices = [hit["title"] for hit in results["hits"][:3]]+["Quit - Try a more specific query."]
    mod_choice = questionary.select("Pick a mod: ", choices=choices).ask()
    index_of_mod = choices.index(mod_choice)
    if index_of_mod == 3:
        click.echo("We recommend knowing the mod beforehand, browse Modrinth first.")
        return
    mod_details = results["hits"][index_of_mod]
    mod_id = mod_details["project_id"]
    r = requests.get(
        f"https://api.modrinth.com/v2/project/{mod_id}/version",
        params={"loaders": f'["{mod_loader}"]', "game_versions": f'["{version}"]'},
    )
    versions = r.json()
    latestVersion = max(versions, key=lambda version: version["date_published"])
    dependencies = []
    for dependency in latestVersion["dependencies"]:
        if dependency["dependency_type"] == "required":
            r = requests.get(
                f"https://api.modrinth.com/v2/project/{dependency['project_id']}",
            )
            results = r.json()
            click.secho(results["title"], bold=True)
            click.echo(results["description"].replace("\n", " "))
    confirm_install = questionary.confirm("Install mod and above dependencies: ").ask()
    if not confirm_install:
        return
    for file in latestVersion["files"]:
        if file["primary"]:
            download_file(
                file["url"],
                os.path.join(dir, f"mods/{file['filename']}"),
                f"Downloading {file['filename']}",
            )
    for dependency in latestVersion["dependencies"]:
        if dependency["dependency_type"] == "required":
            if dependency["version_id"] != None:
                r = requests.get(f"https://api.modrinth.com/v2/version/{dependency['version_id']}")
                results = r.json()
                files = results["files"]
            else:
                r = requests.get(
                    f"https://api.modrinth.com/v2/project/{dependency['project_id']}/version",
                    params={"loaders": f'["{mod_loader}"]', "game_versions": f'["{version}"]'},
                )
                versions = r.json()
                latestVersion = max(versions, key=lambda version: version["date_published"])
                files = latestVersion["files"]
            for file in files:
                if file["primary"]:
                    download_file(
                        file["url"],
                        os.path.join(dir, f"mods/{file['filename']}"),
                        f"Downloading {file['filename']}",
                    )
