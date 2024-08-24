import requests
import json
import mysql.connector
from mysql.connector import Error, IntegrityError
import logging
import pandas as pd
import random
import time

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
            print("Failed to close the database connection.")

    def check_ticket_exists_in_tickets_texts(self, ticket_id):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                query = "SELECT COUNT(*) FROM tickets_texts_cleaned WHERE id = %s;"

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

                query = "SELECT COUNT(*) FROM tickets_texts_cleaned;"

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
        
        query = "SELECT id, text FROM tickets_texts_cleaned WHERE id = %s;"
        
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

    def read_ticket_category(self, ticket_id):
        if self.connection is None:
            print("No connection to the database.")
            return 'Incident'
        
        query = "SELECT category FROM tickets WHERE id = %s;"
        
        category_mapping = {
            'INC': 'Incident',
            'SRQ': 'Request',
            'RFC': 'Request',
            'CHI': 'Request',
            'CHR': 'Request'
        }
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (ticket_id,))
            category = cursor.fetchone()
            
            cursor.close()
            
            if category:
                category_code = category[0]
                return category_mapping.get(category_code, 'Incident')
            else:
                return 'Incident'
        except Error as e:
            print(f"Error: {e}")
            return 'Incident'


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Read configuration file
    with open('config.json', 'r') as file:
        config = json.load(file)

    db = DB(config)

    ticket_id = 11851846 # 01.06.2024
    
    ticket_counter = db.get_tickets_counter()
    print(f"Cleaned ticket texts: {ticket_counter}")

    question_prompts = [
        "The following text is an IT {CATEGORY} ticket. Please summarize the ticket by focusing on the issue, including the type, affected systems or components, potential causes, and the impact on users or operations. The summary should be concise (no more than five sentences), maintaining a technical tone suitable for a general audience of IT professionals. Use present tense and english language. Begin directly with the summary, avoiding any introductory or closing remarks.",
        "The following text is an IT {CATEGORY} ticket. Please summarize the ticket by focusing on the issue. The summary should be concise (no more than four sentences), maintaining a technical tone suitable for a general audience of IT professionals. Use present tense and english language."
    ]

    answer_prompts = [
        "The following text is an IT {CATEGORY} ticket. Summarize the steps required to resolve the issue, including any commands, programs, scripts, or configurations that can be helpful. Present the solution as actionable steps that can be applied to solve the incident, focusing solely on the resolution process without referencing the original problem. The summary should be concise (no more than five sentences) and maintain a technical tone suitable for general application. Use present tense and english language. Begin directly with the summary, avoiding any introductory or closing remarks.",
        "The following text is an IT {CATEGORY} ticket. Summarize the steps required to resolve the issue, including any step and hints that can be helpful. Present the solution as actionable steps without referencing the original problem. The summary should be concise (no more than four sentences). Use present tense and english language."
    ]

    def trim_text(text, max_length=2048):
        """Trims the text to the maximum allowed length without cutting off words."""
        if len(text) > max_length:
            split_pos = text.rfind(' ', 0, max_length)  # Try to trim at the last space before max_length
            if split_pos == -1:
                split_pos = max_length  # If no space found, trim at max_length
            return text[:split_pos].strip()
        return text

    def make_api_call(url, headers, body, max_retries=3, timeout_seconds=5):
        retries = 0
        while retries < max_retries:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(body), timeout=timeout_seconds)
                if response.status_code == 200:
                    return response.json().get('response', None), True
                elif response.status_code == 500:
                    print(f"Server error (500). Retry {retries + 1}/{max_retries}...")
                    return None, False  # Indicate that a 500 error occurred
                else:
                    print(f"Failed to call API. Status code: {response.status_code}")
                    print("Response:", response.text)
                    break 
            except requests.exceptions.Timeout:
                print(f"API call timed out. Retry {retries + 1}/{max_retries}...")
            
            retries += 1
            sleep_time = timeout_seconds * (2 ** retries)
            print(f"Sleeping for {sleep_time} seconds before retrying...")
            time.sleep(sleep_time)

        print("Exceeded maximum retries. Skipping this request.")
        return None, False

    def process_ticket(url, headers, prompt, cleaned_text, model="llama3.1", max_length=2048):
        body = {
            "model": model,
            "prompt": prompt + "\n\n" + cleaned_text,
            "stream": False
        }
        
        response, success = make_api_call(url, headers, body)
        
        if not success:
            trimmed_text = trim_text(cleaned_text, max_length)
            print(f"Retrying with trimmed text ({len(trimmed_text)} characters)...")
            
            body = {
                "model": model,
                "prompt": prompt + "\n\n" + trimmed_text,
                "stream": False
            }
            
            response, success = make_api_call(url, headers, body)
        
        return response



    for counter in range(ticket_counter):
        if not db.check_ticket_exists_in_tickets_summary(ticket_id):
            print(f"Process: {ticket_id}")
            if db.check_ticket_exists_in_tickets_texts(ticket_id):
                ticket_df = db.read_cleaned_ticket(ticket_id)
                if not ticket_df.empty:
                    cleaned_text = ticket_df.loc[0, 'text']

                    ticket_category = db.read_ticket_category(ticket_id)

                    # Select random prompts
                    question_prompts = [p.format(CATEGORY=ticket_category) for p in question_prompts]
                    answer_prompts = [p.format(CATEGORY=ticket_category) for p in answer_prompts]
                    question_prompt = random.choice(question_prompts)
                    answer_prompt = random.choice(answer_prompts)

                    url = "http://devcontainer_ollama:11434/api/generate"

                    headers = {
                        "Content-Type": "application/json"
                    }

                    # API call for question
                    question = process_ticket(url, headers, question_prompt, cleaned_text)
                    if not question:
                        continue  # Skip to next ticket if API call fails

                    print("question: " + question)

                    # API call for answer
                    answer = process_ticket(url, headers, answer_prompt, cleaned_text)
                    if not answer:
                        continue  # Skip to next ticket if API call fails

                    print("answer: " + answer)

                    db.insert_summed_text(ticket_id, question, answer)
        else:
            print(f"Ticket ID {ticket_id} already exists in tickets_summary.")
        ticket_id = ticket_id - 1
