import os
import hashlib
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print

console = Console()

def suggest_directories():
    """Suggests directories if the user enters an invalid path."""
    dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    if dirs:
        console.print("\n[bold yellow]Suggested directories:[/bold yellow]")
        for d in dirs:
            console.print(f" - [cyan]{d}[/cyan]")

def get_file_hash(file_path):
    """Compute MD5 hash of a file."""
    hasher = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest(), None  # Return hash and no error
    except Exception as e:
        return None, str(e)  # Return None and error message

def find_duplicates(directory):
    """Find duplicate files in the given directory with a progress bar."""
    files_hash = {}
    duplicates = []
    errors = []

    all_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            all_files.append(os.path.join(root, file))

    for file_path in track(all_files, description="[cyan]Scanning files...[/cyan]"):
        file_hash, error = get_file_hash(file_path)
        
        if error:
            errors.append((file_path, error))  # Collect errors for later display
            continue  # Skip to next file

        if file_hash:
            if file_hash in files_hash:
                duplicates.append((file_path, files_hash[file_hash]))
            else:
                files_hash[file_hash] = file_path

    return duplicates, errors

if __name__ == "__main__":
    console.print("[bold cyan]Duplicate File Finder[/bold cyan]", style="bold underline")

    while True:
        directory = prompt("Enter the directory to scan for duplicates: ", completer=PathCompleter())
        
        # Expand ~ to absolute path
        directory = os.path.abspath(os.path.expanduser(directory))

        if os.path.exists(directory) and os.path.isdir(directory):
            break  # Valid directory, proceed
        else:
            console.print("[red]Error: Directory does not exist.[/red]")
            suggest_directories()

    duplicates, errors = find_duplicates(directory)

    if duplicates:
        console.print("\n[bold yellow]Duplicate files found:[/bold yellow]\n")

        # Create a table for better visualization
        table = Table(title="Duplicate Files", show_lines=True)
        table.add_column("File 1", justify="left", style="cyan", overflow="fold")
        table.add_column("File 2", justify="left", style="magenta", overflow="fold")

        for file1, file2 in duplicates:
            table.add_row(file1, file2)

        console.print(table)
    else:
        console.print("\n[green]No duplicate files found.[/green]")

    # Display errors in a formatted table
    if errors:
        console.print("\n[bold red]Errors Encountered:[/bold red]\n")
        
        error_table = Table(title="File Processing Errors", show_lines=True)
        error_table.add_column("File Path", justify="left", style="red", overflow="fold")
        error_table.add_column("Error Message", justify="left", style="yellow", overflow="fold")

        for file_path, error_message in errors:
            error_table.add_row(file_path, error_message)

        console.print(error_table)
