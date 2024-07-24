import mysql.connector
from mysql.connector import Error, IntegrityError
import json
import re
import logging
import pandas as pd

def should_skip_line(line, conditions):
    return any(condition(line) for condition in conditions)

def write_string_to_json_file(string, output_file_path):
    json_body = {"content": string}
    with open(output_file_path, 'w') as json_file:
        json.dump(json_body, json_file, indent=4)

# Condition functions
def starts_with_datetime(line):
    datetime_pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}")
    return bool(datetime_pattern.match(line))

def starts_with_keyword(line, keyword):
    return line.startswith(keyword)

def is_empty_line(line):
    return not line.strip()

# Define conditions for skipping lines
conditions = [
    starts_with_datetime,
    lambda line: starts_with_keyword(line, "____________________") ,
    lambda line: starts_with_keyword(line, "Statusprotokoll") ,
    lambda line: starts_with_keyword(line, "Bearbeiter/Processor:") ,
    lambda line: starts_with_keyword(line, "Priority:") ,
    lambda line: starts_with_keyword(line, "Support Team:") ,
    lambda line: starts_with_keyword(line, "Status:") ,
    lambda line: starts_with_keyword(line, "Kategorie/Category:") ,
    lambda line: starts_with_keyword(line, "Interne Notiz") ,
    lambda line: starts_with_keyword(line, "Info aus Kunde") ,
    lambda line: starts_with_keyword(line, "Priorität/Priority:") ,
    lambda line: starts_with_keyword(line, "Info aus Kunde") ,
    lambda line: starts_with_keyword(line, "Bearbeiter:") ,
    lambda line: starts_with_keyword(line, "Antwort an Kunden") ,
    lambda line: starts_with_keyword(line, "Bitte übernehmen.") ,
    is_empty_line
]


class DB:
    def __init__(self, config):
        self.user = config.get('db-user')
        self.password = config.get('db-password')
        self.host = config.get('db-host')
        self.database = config.get('db-database')
        
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
        
    def __del__(self):
        if self.connection.is_connected():
            cursor = self.connection.cursor()
            cursor.close()
            self.connection.close()
            print("Connection to the database was successfuly closed.")
        else:
            print("Failed to close to the database connection.")

    def check_ticket_exists_in_db(self, ticketid):

        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = """
                SELECT COUNT(*) FROM tickets WHERE id = %s;
                """

                # Execute the query
                cursor.execute(query,(ticket_id,))
                counter = cursor.fetchone()[0]

                if counter == 1:
                    return True
                else:
                    return False
            else:
                print("Failed to connect to the database.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()
                #self.connection.close()
                #print("MySQL connection is closed")

    def get_tickets_counter(self):

        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = """
                SELECT COUNT(*) FROM tickets;
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

    def read_ticket(self, ticketid):
        if self.connection is None:
            print("No connection to the database.")
            return None
        
        query = "SELECT id, text FROM tickets WHERE id = %s;"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query,(ticket_id,))
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
    
    ticket_id = 11851846 # 01.06.2024
    ticket_counter = db.get_tickets_counter()
    print(f"Rows: {ticket_counter}")

    for i in range(ticket_counter):
        ticket_df = db.read_ticket(ticketid=ticket_id)
        print(ticket_df.head())
        # TODO cleanup and save to new table

        ticket_id = ticket_id - 1
