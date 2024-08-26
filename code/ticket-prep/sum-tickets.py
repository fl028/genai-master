import requests
import json
import mysql.connector
from mysql.connector import Error, IntegrityError
import logging
import pandas as pd
import random

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
            'INC': 'incident',
            'SRQ': 'request',
            'RFC': 'request',
            'CHI': 'request',
            'CHR': 'request'
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

    trim_keywords = [
        "**Summary**",
        "Here",
        "Here's",
        "Incident Summary",
        "Issue summary"
    ]
    
    retry_keywords = [
        "Der",
        "Die",
        "Das",
        "Eine",
        "Ein",
        "Entschuldigung",
        "Entspricht",
        "Es",
        "Hallo",
        "Hier",
        "Keine",
        "Ich",
        "Frau",
        "I'll work",
        "I can",
        "I can't",
        "I don't",
        "Lo siento",
        "No issue",
        "No IT",
        "Unfortunately"
    ]

    def trim_response(response, trim_keywords):
        lines = response.split('\n')
        first_line = lines[0].strip()
        if any(first_line.startswith(keyword) for keyword in trim_keywords):
            lines.pop(0)
        return '\n'.join(lines).strip()

    def should_retry(response, retry_keywords):
        lines = response.split('\n', 1)
        first_line = lines[0].strip() if lines else ""
        return any(first_line.startswith(keyword) for keyword in retry_keywords)

    def make_api_call(url, headers, body, max_retries=5):
        retries = 0
        use_large_context = False

        while retries < max_retries:
            try:
                if use_large_context:
                    body["options"] = {"num_ctx": 16384}  # Use increased context

                response = requests.post(url, headers=headers, data=json.dumps(body))
                if response.status_code == 200:
                    api_response = response.json().get('response', None)
                    
                    if should_retry(api_response, retry_keywords):
                        print(f"Retrying API call due to unwanted start ...")
                        retries += 1
                        use_large_context = True  # Ensure larger context is used on retry
                        continue
                    
                    trimmed_response = trim_response(api_response, trim_keywords)
                    return trimmed_response, True
                elif response.status_code == 500:
                    print(f"Failed to call API. Status code: {response.status_code}")
                    print("Response:", response.text)
                    print(f"Server error (500). Retry {retries + 1}/{max_retries} with increased context...")
                    use_large_context = True  # Switch to larger context on server error
                else:
                    print(f"Failed to call API. Status code: {response.status_code}")
                    print("Response:", response.text)
                    break
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")
                break
            
            retries += 1

        print("Exceeded maximum retries. Skipping this request.")
        return None, False

    def process_ticket(url, headers, prompt, cleaned_text, model="llama3.1"):
        body = {
            "model": model,
            "prompt": prompt + "\n\n" + cleaned_text,
            "stream": False,
            "options": {"num_ctx": 4096}  # Default context size
        }
        
        response, success = make_api_call(url, headers, body)
        
        if not success:
            response, success = make_api_call(url, headers, body)
        
        return response

    for counter in range(ticket_counter):
        if not db.check_ticket_exists_in_tickets_summary(ticket_id):
            print(f"### Process: {ticket_id} ###")
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
