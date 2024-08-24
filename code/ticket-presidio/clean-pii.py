import logging
import json
import pandas as pd
import mysql.connector
from mysql.connector import Error
import spacy
import re

nlp = spacy.load("de_core_news_lg")

name_regex = re.compile(r'\b(?:[A-ZÄÖÜ][a-zäöüß]+(?:[-\' ][A-ZÄÖÜ][a-zäöüß]+)?)+\b')

discard_patterns = re.compile(r'[^\w\säöüÄÖÜß\'-]|[_%$#@!&]')

def is_valid_name(name):
    return bool(name_regex.fullmatch(name))

def is_discardable_name(name):
    return bool(discard_patterns.search(name))

def anonymize_pii(text, config):
    doc = nlp(text)
    anonymized_text = text
    
    person_names = set()
    discarded_names = set()
    false_recognized_names = set(config.get("false_recognized_names", []))

    for ent in doc.ents:
        if ent.label_ == "PER":
            name = ent.text
            if is_discardable_name(name) or name in false_recognized_names:
                discarded_names.add(name)
            elif is_valid_name(name):
                person_names.add(name)
            else:
                discarded_names.add(name)

    if person_names:
        print("Detected valid person names:")
        for name in person_names:
            print(f"- {name}")

    if discarded_names:
        print("Discarded names (containing special characters, false recognized, or not matching regex):")
        for name in discarded_names:
            print(f"- {name}")

    # Replace valid person names with placeholders in the text
    for name in person_names:
        anonymized_text = anonymized_text.replace(name, "")

    config.setdefault("valid_names", []).extend(person_names)
    config.setdefault("discarded_names", []).extend(discarded_names)
    config["valid_names"] = list(set(config["valid_names"]))
    config["discarded_names"] = list(set(config["discarded_names"]))

    return anonymized_text

def update_config_file(config, file_path):
    with open(file_path, 'w') as file:
        json.dump(config, file, indent=4)

class DB:
    def __init__(self, config):
        self.user = config.get('db-user')
        self.password = config.get('db-password')
        self.host = config.get('db-host')
        self.database = config.get('db-database')
        self.connection = mysql.connector.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def __del__(self):
        if self.connection.is_connected():
            cursor = self.connection.cursor()
            cursor.close()
            self.connection.close()

    def check_ticket_exists_in_tickets_texts_cleaned(self, ticket_id):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                query = "SELECT COUNT(*) FROM tickets_texts_cleaned WHERE id = %s;"
                cursor.execute(query, (ticket_id,))
                counter = cursor.fetchone()[0]
                return counter == 1
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()

    def get_tickets_counter(self):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                query = "SELECT COUNT(*) FROM tickets_texts;"
                cursor.execute(query)
                counter = cursor.fetchone()[0]
                return int(counter)
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()

    def read_ticket(self, ticket_id):
        if self.connection is None:
            return None
        query = "SELECT id, text FROM tickets_texts WHERE id = %s;"
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

                query = "INSERT INTO tickets_texts_cleaned (id, text) VALUES (%s, %s);"
                cursor.execute(query, (ticket_id, cleaned_text))
                self.connection.commit()
                print(f"Inserted cleaned text for ticket ID {ticket_id}.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config_file_path = 'config.json'
    with open(config_file_path, 'r') as file:
        config = json.load(file)

    db = DB(config)

    ticket_id = 11851846 # 01.06.2024

    ticket_counter = db.get_tickets_counter()
    print(f"Rows: {ticket_counter}")

    for counter in range(ticket_counter):
        if not db.check_ticket_exists_in_tickets_texts_cleaned(ticket_id):
            ticket_df = db.read_ticket(ticket_id)
            if ticket_df is not None and not ticket_df.empty:
                raw_text = ticket_df.loc[0, 'text']
                cleaned_text = anonymize_pii(raw_text, config)
                db.insert_cleaned_text(ticket_id, cleaned_text)
                update_config_file(config, config_file_path)
            else:
                print(f"No data found for ticket ID {ticket_id}.")
        else:
            print(f"Ticket ID {ticket_id} already exists in tickets_texts_cleaned.")

        ticket_id = ticket_id - 1
