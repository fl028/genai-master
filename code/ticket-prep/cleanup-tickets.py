import mysql.connector
from mysql.connector import Error, IntegrityError
import json
import re
import logging
import pandas as pd

def should_skip_line(line, conditions):
    return any(condition(line) for condition in conditions)

def clean_text(text, conditions):
    cleaned_lines = []
    for line in text.split('\n'):
        if not should_skip_line(line, conditions):
            cleaned_lines.append(line.strip())
    return '\n'.join(cleaned_lines)

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
    lambda line: starts_with_keyword(line, "____________________"),
    lambda line: starts_with_keyword(line, "Statusprotokoll"),
    lambda line: starts_with_keyword(line, "Bearbeiter/Processor:"),
    lambda line: starts_with_keyword(line, "Priority:"),
    lambda line: starts_with_keyword(line, "Support Team:"),
    lambda line: starts_with_keyword(line, "Status:"),
    lambda line: starts_with_keyword(line, "Kategorie/Category:"),
    lambda line: starts_with_keyword(line, "Interne Notiz"),
    lambda line: starts_with_keyword(line, "Info aus Kunde"),
    lambda line: starts_with_keyword(line, "Priorität/Priority:"),
    lambda line: starts_with_keyword(line, "Info aus Kunde"),
    lambda line: starts_with_keyword(line, "Bearbeiter:"),
    lambda line: starts_with_keyword(line, "Antwort an Kunden"),
    lambda line: starts_with_keyword(line, "Bitte übernehmen."),
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
            print("Connection to the database was successfully closed.")
        else:
            print("Failed to close to the database connection.")

    def check_ticket_exists_in_tickets_texts(self, ticket_id):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = "SELECT COUNT(*) FROM tickets_texts WHERE id = %s;"

                cursor.execute(query, (ticket_id,))
                counter = cursor.fetchone()[0]

                return counter == 1
            else:
                print("Failed to connect to the database.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()

    def get_tickets_counter(self):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = "SELECT COUNT(*) FROM tickets;"

                cursor.execute(query)
                counter = cursor.fetchone()[0]
                return int(counter)
            else:
                print("Failed to connect to the database.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()

    def read_ticket(self, ticket_id):
        if self.connection is None:
            print("No connection to the database.")
            return None
        
        query = "SELECT id, text FROM tickets WHERE id = %s;"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (ticket_id,))
            rows = cursor.fetchall()
            
            column_names = [i[0] for i in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)
            
            cursor.close()
            
            return df
        except Error as e:
            print(f"Error: {e}")
            return None

    def insert_cleaned_text(self, ticket_id, cleaned_text):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = "INSERT INTO tickets_texts (id, text) VALUES (%s, %s);"
                cursor.execute(query, (ticket_id, cleaned_text))
                self.connection.commit()
                print(f"Inserted cleaned text for ticket ID {ticket_id}.")
        except IntegrityError:
            print(f"Ticket ID {ticket_id} already exists in tickets_texts.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Read configuration file
    with open('config.json', 'r') as file:
        config = json.load(file)

    db = DB(config)

    ticket_id = 11851846 # 01.06.2024
    
    ticket_counter = db.get_tickets_counter()
    print(f"Rows: {ticket_counter}")

    for counter in range(ticket_counter):
        if not db.check_ticket_exists_in_tickets_texts(ticket_id):
            ticket_df = db.read_ticket(ticket_id)
            if not ticket_df.empty:
                raw_text = ticket_df.loc[0, 'text']
                cleaned_text = clean_text(raw_text, conditions)
                db.insert_cleaned_text(ticket_id, cleaned_text)
        else:
            print(f"Ticket ID {ticket_id} already exists in tickets_texts.")

        ticket_id = ticket_id - 1
