import mysql.connector
from mysql.connector import Error, IntegrityError
import json
import re
import logging
import pandas as pd

def starts_with_datetime(line):
    datetime_pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4}[\t\s]+\d{2}:\d{2}:\d{2}")
    return bool(datetime_pattern.match(line))

def contains_telephone_number(line):
    phone_pattern = re.compile(r'''
        (\+?\d{1,4}[\s-]?)?  # Optional international code
        (\(?\d{2,4}\)?[\s-]?)  # Area code with optional parentheses
        \d{1,4}[\s-]?         # Main number segment 1
        \d{1,4}[\s-]?         # Main number segment 2
        \d{1,4}               # Main number segment 3
        (?:[\s-]?\d{1,4})?    # Optional extension
        (?:[\s-]?\d{1,4})?    # Optional additional segment
    ''', re.VERBOSE)
    return bool(phone_pattern.search(line))

def contains_email(line):
    email_pattern = re.compile(r'''
        [a-zA-Z0-9._%+-]+       # Local part
        @                       # @ symbol
        [a-zA-Z0-9.-]+          # Domain part
        \.[a-zA-Z]{2,}          # Top-level domain
    ''', re.VERBOSE)
    return bool(email_pattern.search(line))

def contains_ip_address(line):
    ip_pattern = re.compile(r'''
        (?:\d{1,3}\.){3}\d{1,3}    # IPv4 address
        |                          # OR
        (?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}   # IPv6 address
    ''', re.VERBOSE)
    return bool(ip_pattern.search(line))

def contains_link(line):
    url_pattern = re.compile(r'''
        https?://[^\s/$.?#].[^\s]*    # Matches URLs with http or https schemes
        |                            # OR
        www\.[^\s/$.?#].[^\s]*        # Matches URLs starting with www
    ''', re.VERBOSE)
    return bool(url_pattern.search(line))

def contains_date(line):
    date_pattern = re.compile(r'''
        \b\d{2}[-/]\d{2}[-/]\d{4}   # MM-DD-YYYY or DD-MM-YYYY
        |                          # OR
        \b\d{4}[-/]\d{2}[-/]\d{2}   # YYYY-MM-DD
        |                          # OR
        \b\d{2}[-/]\d{2}[-/]\d{2}   # MM-DD-YY or DD-MM-YY
    ''', re.VERBOSE)
    return bool(date_pattern.search(line))

def starts_with_keyword(line, keywords):
    return any(line.strip().startswith(keyword) for keyword in keywords)

def is_empty_line(line):
    return not line.strip()

def replace_specific_terms(text, specific_terms):
    for term, replacement in specific_terms.items():
        text = re.sub(r'\b{}\b'.format(re.escape(term)), replacement, text, flags=re.IGNORECASE)
    return text

def clean_text(text, line_conditions, word_conditions, keywords, term_dict):
    cleaned_lines = []
    for line in text.split('\n'):
        if not any(condition(line) for condition in line_conditions):
            words = line.split()
            cleaned_words = [word for word in words if not any(condition(word) for condition in word_conditions)]
            cleaned_line = ' '.join(cleaned_words)
            cleaned_lines.append(cleaned_line)

    cleaned_text = '\n'.join(cleaned_lines)
    
    # Replace specific terms
    cleaned_text = replace_specific_terms(cleaned_text, term_dict)
    
    # Replace keywords in the entire cleaned text
    for keyword in keywords:
        cleaned_text = re.sub(r'\b{}\b'.format(re.escape(keyword)), '', cleaned_text)

    # Clean up any extra spaces and empty lines after keyword replacement
    cleaned_text = '\n'.join(line.strip() for line in cleaned_text.splitlines() if line.strip())
    
    return cleaned_text

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
    
    def read_ticket_title(self, ticket_id):
        if self.connection is None:
            print("No connection to the database.")
            return None
        
        query = "SELECT title FROM tickets WHERE id = %s;"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (ticket_id,))
            title = cursor.fetchone()
            
            cursor.close()
            
            return title[0] if title else None
        except Error as e:
            print(f"Error: {e}")
            return None
        
    def read_ticket_category(self, ticket_id):
        if self.connection is None:
            print("No connection to the database.")
            return None
        
        query = "SELECT category FROM tickets WHERE id = %s;"
        
        # Define the category mapping
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
                # Get the actual category code
                category_code = category[0]
                # Map the category code to the descriptive name
                return category_mapping.get(category_code, 'Unknown Category')
            else:
                return None
        except Error as e:
            print(f"Error: {e}")
            return None



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with open('config.json', 'r') as file:
        config = json.load(file)

    keywords = config.get('keywords', [])
    specific_terms = config.get('specific_terms', {})

    line_conditions = [
        starts_with_datetime,
        lambda line: starts_with_keyword(line, keywords),
        is_empty_line,
        contains_telephone_number,
    ]

    word_conditions = [
        contains_email,
        contains_ip_address,
        contains_link,
        contains_date
    ]

    db = DB(config)

    ticket_id = 11851846 # 01.06.2024
    
    ticket_counter = db.get_tickets_counter()
    print(f"Rows: {ticket_counter}")

    for counter in range(ticket_counter):
        if not db.check_ticket_exists_in_tickets_texts(ticket_id):
            ticket_df = db.read_ticket(ticket_id)
            if not ticket_df.empty:
                title = db.read_ticket_title(ticket_id)
                category = db.read_ticket_category(ticket_id)
                raw_text = ticket_df.loc[0, 'text']
                
                if category and title:
                    # Prepend the category and title to the cleaned text
                    raw_text = f"{category}\nTitle: {title}\n\n{raw_text}"

                cleaned_text = clean_text(raw_text, line_conditions, word_conditions, keywords, specific_terms)

                db.insert_cleaned_text(ticket_id, cleaned_text)
        else:
            print(f"Ticket ID {ticket_id} already exists in tickets_texts.")

        ticket_id = ticket_id - 1
