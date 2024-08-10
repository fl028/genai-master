import logging
import json
import pandas as pd
import mysql.connector
from mysql.connector import Error
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from transformers import pipeline

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

transformer_nlp = pipeline(
    "ner",
    model="xlm-roberta-large-finetuned-conll03-english",
    tokenizer="xlm-roberta-large-finetuned-conll03-english",
    device=0
)

ANONYMIZE_ENTITY_TYPES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "DATE_TIME", "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS"
]

def analyze_with_transformer(text):
    results = transformer_nlp(text)
    presidio_results = []
    for ent in results:
        entity_type = ent['entity'].split("-")[-1]
        if entity_type in ANONYMIZE_ENTITY_TYPES:
            presidio_results.append(
                RecognizerResult(
                    entity_type=entity_type,
                    start=ent['start'],
                    end=ent['end'],
                    score=ent['score']
                )
            )
    return presidio_results

def anonymize_pii(text):
    transformer_results = analyze_with_transformer(text)
    analyzer_results = analyzer.analyze(
        text=text, 
        entities=ANONYMIZE_ENTITY_TYPES, 
        language="en"
    )
    all_results = analyzer_results + transformer_results
    anonymizer_results = [
        RecognizerResult(
            entity_type=result.entity_type,
            start=result.start,
            end=result.end,
            score=result.score
        )
        for result in all_results
        if result.entity_type in ANONYMIZE_ENTITY_TYPES
    ]
    anonymized_text = anonymizer.anonymize(text=text, analyzer_results=anonymizer_results)
    return anonymized_text

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

    def check_ticket_exists_in_tickets_texts(self, ticket_id):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                query = "SELECT COUNT(*) FROM tickets_texts WHERE id = %s;"
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
                query = "SELECT COUNT(*) FROM tickets;"
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

    def update_cleaned_text(self, ticket_id, cleaned_text):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                query = "UPDATE tickets_texts SET text = %s WHERE id = %s;"
                cursor.execute(query, (cleaned_text, ticket_id))
                self.connection.commit()
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with open('config.json', 'r') as file:
        config = json.load(file)

    db = DB(config)

    ticket_id = 11851846

    ticket_counter = db.get_tickets_counter()
    print(f"Rows: {ticket_counter}")

    for counter in range(ticket_counter):
        ticket_df = db.read_ticket(ticket_id)
        if ticket_df is not None and not ticket_df.empty:
            raw_text = ticket_df.loc[0, 'text']
            cleaned_text = anonymize_pii(raw_text)
            db.update_cleaned_text(ticket_id, cleaned_text)
        else:
            print(f"No data found for ticket ID {ticket_id}.")

        ticket_id = ticket_id - 1
