def handle(args, console):
    """
    Print the CLI version, author, and repository information.
    """
    version = "1.0.0"
    author = "DiffSync Team"
    repo_url = "https://github.com/your-org/diffsync"

    console.print(f"[bold magenta]DiffSync CLI[/bold magenta] [bold yellow]v{version}[/bold yellow]")
    console.print(f"Developed by [bold cyan]{author}[/bold cyan]")
    console.print(f"Source: [underline blue]{repo_url}[/underline blue]")
