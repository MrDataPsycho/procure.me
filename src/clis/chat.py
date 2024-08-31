import typer
import requests
import threading
from rich.table import Table
from rich.console import Console

app = typer.Typer()

# Initialize Rich console for printing
console = Console()

def send_query_and_display_table(query: str):
    """Sends a POST request to the server and displays the response in a table format."""
    url = "http://127.0.0.1:5000/api/v1/search"
    data = {"search_input": query}
    
    try:
        # Send POST request
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise an error for bad responses

        # Parse JSON response
        response_json = response.json()
        
        # Extract response data
        query_text = response_json.get('query', '')
        response_data = response_json.get('response_data', [])

        # Create a rich table
        table = Table(title=f"Search Results for: '{query_text}'")

        # Define table columns
        table.add_column("L1", justify="right", style="cyan", no_wrap=True)
        table.add_column("L1 Description", style="magenta")
        table.add_column("L2", justify="right", style="cyan", no_wrap=True)
        table.add_column("L2 Description", style="magenta")
        table.add_column("L3", justify="right", style="cyan", no_wrap=True)
        table.add_column("L3 Description", style="magenta")

        # Populate table rows with the response data
        for item in response_data:
            table.add_row(
                str(item['l1']),
                item['l1_desc'],
                str(item['l2']),
                item['l2_desc'],
                str(item['l3']),
                item['l3_desc']
            )

        # Print the table to the console
        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")

def user_input_thread():
    """Continuously prompt the user for input and send queries."""
    while True:
        query = input("Enter your query (or type 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        send_query_and_display_table(query)

@app.command()
def start():
    """Start the CLI for sending queries to the server."""
    # Launch user input thread
    input_thread = threading.Thread(target=user_input_thread)
    input_thread.start()
    input_thread.join()  # Wait for the input thread to finish

if __name__ == "__main__":
    """Example: python search_cli.py start"""
    app()
