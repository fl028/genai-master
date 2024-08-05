import logging
import json
import mysql.connector
from mysql.connector import Error, IntegrityError
import pandas as pd

class DB:
    def __init__(self, config):
        self.user = config.get('db-user')
        self.password = config.get('db-password')
        self.host = config.get('db-host')
        self.database = config.get('db-database')
        
        try:
            # Connect to the database
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )

            if self.connection.is_connected():
                print("Connection to the database was successful.")
            else:
                print("Failed to connect to the database.")
        except Error as e:
            print(f"Error: {e}")
            self.connection = None
        
    def __del__(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Connection to the database was successfully closed.")
        else:
            print("Failed to close the database connection.")
    
    def get_tickets_counter(self):

        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = """
                SELECT COUNT(*) FROM tickets_summary;
                """

                # Execute the query
                cursor.execute(query,())
                counter = cursor.fetchone()[0]
                return int(counter)
            else:
                print("Failed to connect to the database.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()

    def read_tickets(self):
        if self.connection is None:
            print("No connection to the database.")
            return None
        
        query = "SELECT id, question, answer FROM tickets_summary"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [i[0] for i in cursor.description]
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=column_names)
            
            cursor.close()
            
            return df
        except Error as e:
            print(f"Error: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  

    # Read configuration file
    with open('config.json', 'r') as file:
        config = json.load(file)

    db = DB(config)
    
    # Read and print the tickets table as a pandas DataFrame
    tickets_df = db.read_tickets()
    ticket_counter = db.get_tickets_counter()
    print(f"Rows: {ticket_counter}")
    print(tickets_df.head())
