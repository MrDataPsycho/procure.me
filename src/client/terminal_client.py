import httpx
import time
from rich.console import Console
from rich.table import Table

API_URL = "http://127.0.0.1:5000/api/v1/search"
console = Console()

def search(term: str):
    """
    Search for a term in the ChromaDB vector database.
    """
    console.print(f"[bold green]Searching for:[/bold green] {term}")

    start_time = time.time()

    # Making the POST request
    try:
        response = httpx.post(API_URL, json={"search_input": term})
    except httpx.RequestError as exc:
        console.print(f"[bold red]An error occurred while requesting {exc.request.url!r}.[/bold red]")
        return

    if response.status_code != 200:
        console.print(f"[bold red]Failed to fetch results: {response.status_code}[/bold red]")
        return

    # Parsing the response
    data = response.json()
    similar_items = data.get("similar", [])

    if not similar_items:
        console.print("[bold red]Cannot find what you are searching for.[/bold red]")
        return

    # Displaying the results in a table
    table = Table(title="Search Results")
    table.add_column("L1", style="cyan", no_wrap=True)
    table.add_column("L1 Description", style="magenta")
    table.add_column("L2", style="cyan")
    table.add_column("L2 Description", style="magenta")
    table.add_column("L3", style="cyan")
    table.add_column("L3 Description", style="magenta")

    for item in similar_items:
        table.add_row(
            str(item["l1"]),
            item["l1_desc"],
            str(item["l2"]),
            item["l2_desc"],
            str(item["l3"]),
            item["l3_desc"],
        )

    console.print(table)

    elapsed_time = time.time() - start_time
    console.print(f"[bold green]Search completed in {elapsed_time:.2f} seconds.[/bold green]")

def main():
    while True:
        try:
            search_term = input("\nEnter your search term (or Ctrl+C to exit): ")
            search(search_term)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Exiting the search application.[/bold yellow]")
            break

if __name__ == "__main__":
    main()
