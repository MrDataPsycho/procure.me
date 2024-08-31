import typer
from rich.table import Table
from rich.console import Console

app = typer.Typer()

@app.command()
def display_table():
    # Sample JSON data
    json_data = [
        {'l1': 10, 'l1_desc': 'Office Equipment', 'l2': 1010, 'l2_desc': 'Files and Stationery', 'l3': 101010, 'l3_desc': 'Pencil, Files, Envelopes for office equipment'},
        {'l1': 20, 'l1_desc': 'IT Goods and Services', 'l2': 2010, 'l2_desc': 'Computers and Peripherals', 'l3': 201010, 'l3_desc': 'Desktop Computers for office workstations'},
        {'l1': 20, 'l1_desc': 'IT Goods and Services', 'l2': 2010, 'l2_desc': 'Computers and Peripherals', 'l3': 201030, 'l3_desc': 'Monitors and Display Screens for computing'}
    ]

    # Create a rich table
    table = Table(title="Commodity Codes")

    # Add columns
    table.add_column("L1", justify="right", style="cyan", no_wrap=True)
    table.add_column("L1 Description", style="magenta")
    table.add_column("L2", justify="right", style="cyan", no_wrap=True)
    table.add_column("L2 Description", style="magenta")
    table.add_column("L3", justify="right", style="cyan", no_wrap=True)
    table.add_column("L3 Description", style="magenta")

    # Add rows to the table from JSON data
    for item in json_data:
        table.add_row(
            str(item['l1']),
            item['l1_desc'],
            str(item['l2']),
            item['l2_desc'],
            str(item['l3']),
            item['l3_desc']
        )

    # Render the table to the console
    console = Console()
    console.print(table)


if __name__ == "__main__":
    app()