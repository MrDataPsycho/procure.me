import typer
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from procureme.configurations.db_connection_config import DbConnectionModel
import os
import pandas as pd


app = typer.Typer()
load_dotenv(".envs/dev.env", override=True)
db_connection = DbConnectionModel(**os.environ)

# Database configuration
DATABASE_URL = db_connection.get_connection_str()

# Create a connection to the database
engine = create_engine(DATABASE_URL)
metadata = MetaData()


def _create_table():
    """Creates the table based on the CSV schema."""
    table = Table(
        "commodity_codes",
        metadata,
        Column("l1", Integer),
        Column("l1_desc", String),
        Column("l2", Integer),
        Column("l2_desc", String),
        Column("l3", Integer, primary_key=True),
        Column("l3_desc", String),
    )
    metadata.create_all(engine)


@app.command()
def create_table():
    """Create a table in the PostgreSQL database."""
    try:
        _create_table()
        typer.echo("Table created successfully.")
    except SQLAlchemyError as e:
        typer.echo(f"Error creating table: {e}")


@app.command()
def insert_data(csv_file: str):
    """Insert data from a CSV file into the PostgreSQL table."""
    try:
        df = pd.read_csv(csv_file, sep="|")
        df.to_sql("commodity_codes", engine, if_exists="append", index=False)
        typer.echo("Data inserted successfully.")
    except SQLAlchemyError as e:
        typer.echo(f"Error inserting data: {e}")
    except FileNotFoundError:
        typer.echo("CSV file not found.")
    except pd.errors.ParserError:
        typer.echo("Error parsing CSV file.")


@app.command()
def delete_data():
    """Delete all data from the PostgreSQL table."""
    try:
        with engine.connect() as connection:
            connection.execute("DELETE FROM commodity_codes;")
        typer.echo("All data deleted successfully.")
    except SQLAlchemyError as e:
        typer.echo(f"Error deleting data: {e}")


@app.command()
def drop_table():
    """Drop the PostgreSQL table and delete all its data."""
    try:
        table = Table("commodity_codes", metadata, autoload_with=engine)
        table.drop(engine)
        typer.echo("Table dropped successfully.")
    except SQLAlchemyError as e:
        typer.echo(f"Error dropping table: {e}")


if __name__ == "__main__":
    """Examples:

    $ python src/clis/manage_table.py create-table
    $ python src/clis/manage_table.py insert-data data/raw/commodity_codes.csv
    $ python src/clis/manage_table.py delete-data
    $ python src/clis/manage_table.py drop-table
    """
    app()
