#!/usr/bin/env python3

import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def list_accounts():
    cmd = ["op", "account", "list", "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout else []

def list_vaults(account_user_id):
    cmd = ["op", "vault", "list", "--account", account_user_id, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout else []

def list_items_in_vault(account_user_id, vault_name):
    cmd = [
        "op",
        "item",
        "list",
        "--vault",
        vault_name,
        "--account",
        account_user_id,
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout else []

def find_duplicates(account_user_id, vault_name):
    """
    Groups items by title. If more than one item shares the same title,
    returns them sorted by updated_at (descending). The top item is the
    most recent, while everything else is considered a duplicate.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Scanning for duplicates...", total=None)
        # Simulate a brief 'load' time for demonstration:
        time.sleep(1)

        items = list_items_in_vault(account_user_id, vault_name)
        item_dict = defaultdict(list)

        for item in items:
            title = item.get("title")
            updated_at = item.get("updated_at")
            item_id = item.get("id")

            # Basic validation to ensure we have the fields
            if title and updated_at and item_id:
                item_dict[title].append(item)

        duplicates = {}
        for title, items_for_title in item_dict.items():
            if len(items_for_title) > 1:
                # Sort by updated_at descending so items[0] is the newest
                sorted_items = sorted(
                    items_for_title,
                    key=lambda x: x["updated_at"],
                    reverse=True
                )
                duplicates[title] = sorted_items

        return duplicates

def select_option(options, prompt):
    """
    A simple text-based selection menu.
    Returns the chosen option.
    """
    console.print(f"\n[bold]{prompt}[/bold]\n")
    for i, option in enumerate(options, 1):
        console.print(f"  {i}. {option}")

    selected_option = None
    while not selected_option:
        option_index = console.input("\nEnter the number of your choice: ")
        if option_index.isdigit() and 1 <= int(option_index) <= len(options):
            selected_option = options[int(option_index) - 1]
        else:
            console.print("[red]Invalid option. Please try again.[/red]")
    return selected_option

@click.command()
@click.argument("vault_name", required=False)
@click.option("--dry", is_flag=True, help="Dry run: print the commands that would be run, without executing them.")
def main(vault_name, dry):
    """
    This script finds and archives duplicate items in a given 1Password vault.

    \b
    - If multiple items share the same title, it keeps only the most recently updated item.
    - It will prompt for your confirmation before archiving.
    - Use --dry to see what would happen without actually archiving.

    Example usage:
      ./dupe.py MyVault   (Archives duplicates in MyVault)
      ./dupe.py           (Prompts to select an account and vault)
      ./dupe.py --dry     (Prompts to select a vault, then just shows what would be done)
    """
    console.print("\n[bold cyan]--- 1Password Duplicate Archiver ---[/bold cyan]")
    console.print("[green]Use --dry to preview archiving actions without executing them.[/green]\n")

    # 1. If vault_name isn't given as an argument, interactively select account and vault
    if not vault_name:
        accounts = list_accounts()
        if not accounts:
            console.print("[red]No accounts found. Please ensure you are signed in to 1Password CLI.[/red]")
            return

        # Prompt user to select an account
        account_options = [f"{a['url']} - {a['email']} - {a['user_uuid']}" for a in accounts]
        chosen_account_str = select_option(account_options, "Select an account:")
        # Extract the user_uuid from the chosen option
        chosen_index = account_options.index(chosen_account_str)
        account_user_id = accounts[chosen_index]["user_uuid"]

        # Prompt user to select a vault
        vaults = list_vaults(account_user_id)
        if not vaults:
            console.print("[red]No vaults found for this account.[/red]")
            return
        vault_options = [v["name"] for v in vaults]
        vault_name = select_option(vault_options, "Select a vault:")
    else:
        # If vault_name was provided, we still need to pick an account if there's more than one.
        accounts = list_accounts()
        if not accounts:
            console.print("[red]No accounts found. Please ensure you are signed in to 1Password CLI.[/red]")
            return

        if len(accounts) == 1:
            # If there's only one account, use it
            account_user_id = accounts[0]["user_uuid"]
        else:
            # Otherwise, prompt the user which account to use
            account_options = [f"{a['url']} - {a['email']} - {a['user_uuid']}" for a in accounts]
            chosen_account_str = select_option(account_options, "Multiple accounts found. Select one:")
            chosen_index = account_options.index(chosen_account_str)
            account_user_id = accounts[chosen_index]["user_uuid"]

    console.print(f"\n[bold]Selected Vault:[/bold] [yellow]{vault_name}[/yellow]")
    duplicates = find_duplicates(account_user_id, vault_name)

    if not duplicates:
        console.print("[green]No duplicates found in this vault.[/green]")
        return

    # 2. Summarize duplicates
    total_duplicates = 0
    for title, items_list in duplicates.items():
        total_duplicates += (len(items_list) - 1)

    console.print(f"\n[yellow]{total_duplicates} duplicate items[/yellow] were found across {len(duplicates)} titles.\n")
    # List each title and how many duplicates
    for title, items_list in duplicates.items():
        console.print(f" • [blue]{title}[/blue]: {len(items_list) - 1} duplicates (of {len(items_list)})")

    # 3. Prompt user whether to archive
    user_input = console.input("\nWould you like to archive these duplicates now? (y/N): ")
    if user_input.lower() != 'y':
        console.print("[red]Aborting: No items were archived.[/red]")
        return

    console.print()  # blank line

    # 4. Archive duplicates
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}")
    ) as progress:
        task = progress.add_task("Archiving duplicates...", total=total_duplicates)

        for title, items_list in duplicates.items():
            # Keep items_list[0], archive the rest
            items_to_archive = items_list[1:]
            for item in items_to_archive:
                item_id = item.get("id")
                item_title = item.get("title")
                cmd = [
                    "op",
                    "item",
                    "delete",
                    item_id,
                    "--vault",
                    vault_name,
                    "--archive",
                    "--account",
                    account_user_id,
                ]
                if dry:
                    console.print(f"[yellow][DRY RUN][/yellow] [bold]Would run:[/bold] {' '.join(cmd)}")
                else:
                    # Actually run the command
                    subprocess.run(cmd, capture_output=True, text=True)

                progress.advance(task)

    console.print("\n[green]Done![/green] The duplicates have been archived.")

if __name__ == "__main__":
    main()
