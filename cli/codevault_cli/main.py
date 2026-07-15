import json
import os
import click
import requests
from rich.console import Console
from rich.table import Table

API_BASE = os.environ.get("CODEVAULT_API_BASE", "http://127.0.0.1:8000")
CONFIG_DIR = os.path.expanduser("~/.codevault")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

console = Console()


def save_token(token: str):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"token": token}, f)


def load_token() -> str | None:
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH) as f:
        return json.load(f).get("token")


def auth_headers() -> dict:
    token = load_token()
    if not token:
        console.print("[red]Not logged in.[/red] Run [bold]codevault login[/bold] first.")
        raise SystemExit(1)
    return {"Authorization": f"Bearer {token}"}


@click.group()
def cli():
    """CodeVault CLI — manage your snippets from the terminal."""
    pass


@cli.command()
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def register(email, password):
    """Create a new CodeVault account."""
    res = requests.post(f"{API_BASE}/users/register", json={"email": email, "password": password})
    if res.status_code == 200:
        console.print(f"[green]Account created for {email}. Now run 'codevault login'.[/green]")
    else:
        console.print(f"[red]Registration failed:[/red] {res.json().get('detail', res.text)}")


@cli.command()
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def login(email, password):
    """Log in and save your session token locally."""
    res = requests.post(f"{API_BASE}/users/login", data={"username": email, "password": password})
    if res.status_code == 200:
        save_token(res.json()["access_token"])
        console.print(f"[green]Logged in as {email}. Token saved to {CONFIG_PATH}[/green]")
    else:
        console.print(f"[red]Login failed:[/red] {res.json().get('detail', res.text)}")


@cli.command(name="list")
@click.option("--q", default="", help="Search query")
@click.option("--limit", default=20, help="Max results to show")
def list_snippets(q, limit):
    """List (and optionally search) your snippets."""
    res = requests.get(f"{API_BASE}/snippets/", params={"q": q, "limit": limit}, headers=auth_headers())
    if res.status_code != 200:
        console.print(f"[red]Error:[/red] {res.text}")
        return

    items = res.json()["items"]
    if not items:
        console.print("[yellow]No snippets found.[/yellow]")
        return

    table = Table(title="Your Snippets")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Language")
    table.add_column("Public")
    table.add_column("Views")

    for item in items:
        table.add_row(
            str(item["id"]), item["title"], item["language"],
            "yes" if item["is_public"] else "no", str(item.get("view_count", 0))
        )
    console.print(table)


@cli.command()
@click.option("--title", prompt=True)
@click.option("--language", prompt=True)
@click.option("--file", "filepath", required=True, type=click.Path(exists=True), help="Path to the code file")
@click.option("--tags", default="", help="Comma-separated tags")
def create(title, language, filepath, tags):
    """Create a snippet from a local file's contents."""
    with open(filepath) as f:
        code = f.read()

    res = requests.post(
        f"{API_BASE}/snippets/",
        json={"title": title, "language": language, "code": code, "tags": tags},
        headers=auth_headers(),
    )
    if res.status_code == 200:
        console.print(f"[green]Created snippet '{title}' (id={res.json()['id']})[/green]")
    else:
        console.print(f"[red]Error:[/red] {res.text}")


@cli.command()
@click.argument("snippet_id", type=int)
def share(snippet_id):
    """Generate (or fetch) a public share link for a snippet."""
    res = requests.post(f"{API_BASE}/snippets/{snippet_id}/share", headers=auth_headers())
    if res.status_code == 200:
        slug = res.json()["share_slug"]
        console.print(f"[green]Share link:[/green] {API_BASE.replace('8000', '5173')}/s/{slug}")
    else:
        console.print(f"[red]Error:[/red] {res.text}")


@cli.command()
@click.argument("snippet_id", type=int)
def delete(snippet_id):
    """Delete a snippet by ID."""
    res = requests.delete(f"{API_BASE}/snippets/{snippet_id}", headers=auth_headers())
    if res.status_code == 200:
        console.print(f"[green]Deleted snippet {snippet_id}[/green]")
    else:
        console.print(f"[red]Error:[/red] {res.text}")


if __name__ == "__main__":
    cli()