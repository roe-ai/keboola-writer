"""
Template Component main class.

"""

import csv
import logging

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException
import requests

from configuration import Configuration


class Component(ComponentBase):
    """
    Extends base class for general Python components. Initializes the CommonInterface
    and performs configuration validation.

    For easier debugging the data folder is picked up by default from `../data` path,
    relative to working directory.

    If `debug` parameter is present in the `config.json`, the default logger is set to verbose DEBUG mode.
    """

    def __init__(self):
        super().__init__()

    def run(self):
        """
        Main execution code
        """

        # ####### EXAMPLE TO REMOVE
        # check for missing configuration parameters
        params = Configuration(**self.configuration.parameters)

        url = "https://api.roe-ai.com/v1/database/query/"
        headers = {"Authorization": f"Bearer {params.api_token}"}

        input_tables = self.get_input_tables_definitions()
        for table in input_tables:
            logging.info(
                f"Received input table: {table.name} with path: {table.full_path}"
            )

        if len(input_tables) == 0:
            raise UserException("No input tables found")

        input_table = input_tables[0]
        with open(input_table.full_path, "r") as inp_file:
            # Write logic writing table using query to the url
            reader = csv.DictReader(inp_file)
            columns = reader.fieldnames

            # Prepare the column string for the CREATE TABLE query
            colstr = "("
            for col in columns:
                colstr += f"`{col}` String, "
            colstr = colstr[:-2] + ")"

            # Create table
            create_query = f"CREATE TABLE IF NOT EXISTS {params.table_name} {colstr} ENGINE = Memory"
            payload = {"query": create_query}
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logging.info("Table created successfully in RoeAI.")
            else:
                logging.error(
                    f"Failed to create table in RoeAI. Status code: {response.status_code}"
                )
                raise UserException("Failed to create table in RoeAI")

            # Insert data
            def _insert_batch(batch):
                values_str = ", ".join(batch)
                insert_query = f"INSERT INTO {params.table_name} VALUES {values_str}"
                payload = {"query": insert_query}
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    logging.error(
                        f"Failed to insert batch. Status code: {response.status_code}"
                    )
                    raise UserException("Failed to insert data into RoeAI")

            batch_size = 1000
            batch = []
            for row in reader:
                values = tuple(row.values())
                batch.append(str(values))

                if len(batch) >= batch_size:
                    _insert_batch(batch)
                    batch = []

            # Insert any remaining rows
            if batch:
                _insert_batch(batch)

            logging.info("Data insertion completed.")


"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
