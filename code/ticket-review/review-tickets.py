import mysql.connector
from mysql.connector import Error, IntegrityError
import json
import logging

class DB:
    def __init__(self, config_path):
        self.config_path = config_path
        with open(config_path, 'r') as file:
            self.config = json.load(file)

        self.user = self.config.get('db-user')
        self.password = self.config.get('db-password')
        self.host = self.config.get('db-host')
        self.database = self.config.get('db-database')
        self.keywords = self.config.get('keywords', [])

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
        query = "SELECT id, text FROM tickets WHERE id = %s;"
        return self._execute_query_single_result(query, (ticket_id,))

    def read_ticket_texts(self, ticket_id):
        query = "SELECT id, text FROM tickets_texts WHERE id = %s;"
        return self._execute_query_single_result(query, (ticket_id,))

    def read_ticket_texts_cleaned(self, ticket_id):
        query = "SELECT id, text FROM tickets_texts_cleaned WHERE id = %s;"
        return self._execute_query_single_result(query, (ticket_id,))

    def read_ticket_summary(self, ticket_id):
        query = "SELECT id, question, answer FROM tickets_summary WHERE id = %s;"
        return self._execute_query_single_result(query, (ticket_id,))

    def update_ticket_summary(self, ticket_id, new_question, new_answer):
        if self.connection is None:
            print("No connection to the database.")
            return None

        query = "UPDATE tickets_summary SET question = %s, answer = %s WHERE id = %s;"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (new_question, new_answer, ticket_id))
            self.connection.commit()
            cursor.close()
            print(f"Ticket summary {ticket_id} updated successfully.")
        except Error as e:
            print(f"Error: {e}")

    def _execute_query_single_result(self, query, params):
        if self.connection is None:
            print("No connection to the database.")
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row
        except Error as e:
            print(f"Error: {e}")
            return None

    def add_keyword(self, new_keyword):
        if new_keyword not in self.keywords:
            self.keywords.append(new_keyword)
            self._update_config_file()
            print(f"Keyword '{new_keyword}' added successfully.")
        else:
            print(f"Keyword '{new_keyword}' already exists in the list.")

    def _update_config_file(self):
        try:
            with open(self.config_path, 'w') as file:
                self.config['keywords'] = self.keywords
                json.dump(self.config, file, indent=4)
            print("Config file updated successfully.")
        except Exception as e:
            print(f"Error updating config file: {e}")

    def iterate_and_update_summaries(self):
        ticket_counter = self.get_tickets_counter()
        print(f"Total Tickets: {ticket_counter}")

        ticket_id = 11851846 # 01.06.2024

        for _ in range(ticket_counter):
            # Stage 1: Read the ticket
            ticket = self.read_ticket(ticket_id)
            if ticket:
                print(f"\nStage 1 - Ticket ID: {ticket[0]}")
                print(f"Original Text: {ticket[1]}")

                # Stage 2: Read the ticket text
                ticket_text = self.read_ticket_texts(ticket_id)
                if ticket_text:
                    print(f"\nStage 2 - Ticket Text ID: {ticket_text[0]}")
                    print(f"Text: {ticket_text[1]}")

                # Stage 3: Read the cleaned ticket text
                ticket_text_cleaned = self.read_ticket_texts_cleaned(ticket_id)
                if (ticket_text_cleaned):
                    print(f"\nStage 3 - Cleaned Ticket Text ID: {ticket_text_cleaned[0]}")
                    print(f"Cleaned Text: {ticket_text_cleaned[1]}")

                # Stage 4: Read and update the ticket summary
                ticket_summary = self.read_ticket_summary(ticket_id)
                if ticket_summary:
                    print(f"\nStage 4 - Ticket Summary ID: {ticket_summary[0]}")
                    print(f"Question: {ticket_summary[1]}")
                    print(f"Answer: {ticket_summary[2]}")

                    while True:
                        action = input("Choose an action: (1) Next Ticket, (2) Change Question or Answer, (3) Add Keyword, (4) Exit: ")

                        if action == '1':
                            break  # Move to the next ticket
                        elif action == '2':
                            new_question = input("Enter the updated question (or press Enter to keep original): ")
                            new_answer = input("Enter the updated answer (or press Enter to keep original): ")

                            # Keep original values if no input is given
                            new_question = new_question.strip() if new_question.strip() != "" else ticket_summary[1]
                            new_answer = new_answer.strip() if new_answer.strip() != "" else ticket_summary[2]
                            self.update_ticket_summary(ticket_id, new_question, new_answer)
                            break  # Move to the next ticket
                        elif action == '3':
                            new_keyword = input("Enter the new keyword to add: ").strip()
                            if new_keyword:
                                self.add_keyword(new_keyword)
                            else:
                                print("Keyword cannot be empty.")
                        elif action == '4':
                            return  # Exit the function (and the script)
                        else:
                            print("Invalid choice. Please select 1, 2, 3, or 4.")
            else:
                print(f"Ticket with ID {ticket_id} not found.")
            
            ticket_id -= 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config_path = 'config.json'
    db = DB(config_path)

    db.iterate_and_update_summaries()
