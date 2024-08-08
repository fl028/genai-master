import requests
import json
import mysql.connector
from mysql.connector import Error, IntegrityError
import logging
import pandas as pd

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

    def check_ticket_exists_in_tickets_summary(self, ticket_id):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = "SELECT COUNT(*) FROM tickets_summary WHERE id = %s;"

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

    def read_cleaned_ticket(self, ticket_id):
        if self.connection is None:
            print("No connection to the database.")
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
        

    def insert_summed_text(self, ticket_id, question, answer):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = "INSERT INTO tickets_summary (id, question, answer) VALUES (%s, %s, %s);"
                cursor.execute(query, (ticket_id, question, answer))
                self.connection.commit()
                print(f"Inserted summary text for ticket ID {ticket_id}.")
        except IntegrityError:
            print(f"Ticket ID {ticket_id} already exists in tickets_summary.")
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
    print(f"Cleaned ticket texts: {ticket_counter}")

    for counter in range(ticket_counter):
        if not db.check_ticket_exists_in_tickets_summary(ticket_id):
            print(f"Process: {ticket_id}")
            if db.check_ticket_exists_in_tickets_texts(ticket_id):
                ticket_df = db.read_cleaned_ticket(ticket_id)
                if not ticket_df.empty:
                    cleaned_text = ticket_df.loc[0, 'text']
                   

                    url = "http://devcontainer_ollama:11434/api/generate"

                    headers = {
                        "Content-Type": "application/json"
                    }

                    body_question = {
                        "model": "llama3.1",
                        "prompt": "The following text is an it incident ticket. I would like you to summarize the ticket text for me in an abstract form (only the incident) so that the incident situation can also be applied to other IT incidents. \n\n Maximum four sentences. Only the plain summary. Start without any phrase at the begnning and ending. \n\n" + cleaned_text,
                        "stream": False
                    }

                    response = requests.post(url, headers=headers, data=json.dumps(body_question))

                    if response.status_code == 200:
                        data = response.json()
                        question = data['response']
                        print("question: " + question)
                    else:
                        print("Failed to call API. Status code:", response.status_code)
                        print("Response:", response.text)


                    body_answer = {
                        "model": "llama3.1",
                        "prompt": "The following text is an it incident ticket. I would like you to summarize the ticket text for me in an abstract form (only the solution) so that the solution can also be applied to other IT incidents. \n\n Maximum four sentences. Only the plain summary. Start without any phrase at the begnning and ending. \n\n" + cleaned_text,
                        "stream": False
                    }

                    response = requests.post(url, headers=headers, data=json.dumps(body_answer))

                    if response.status_code == 200:
                        data = response.json()
                        answer = data['response']
                        print("answer: " + answer)
                    else:
                        print("Failed to call API. Status code:", response.status_code)
                        print("Response:", response.text)

                    
                    db.insert_summed_text(ticket_id,question,answer)
        else:
            print(f"Ticket ID {ticket_id} already exists in tickets_summary.")
        ticket_id = ticket_id - 1



