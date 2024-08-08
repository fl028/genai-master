import json
import mysql.connector
from mysql.connector import Error
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

    def get_summary_data(self):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                query = "SELECT id, question, answer FROM tickets_summary;"
                cursor.execute(query)
                rows = cursor.fetchall()
                
                column_names = [i[0] for i in cursor.description]
                df = pd.DataFrame(rows, columns=column_names)
                
                cursor.close()
                
                return df
            else:
                print("Failed to connect to the database.")
                return None
        except Error as e:
            print(f"Error: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Read configuration file
    with open('config.json', 'r') as file:
        config = json.load(file)

    db = DB(config)
    
    # Fetch the summary data from the database
    df = db.get_summary_data()
    
    if df is not None:
        # Convert DataFrame to JSON format
        data = df.to_dict(orient='records')
        
        # Write data to JSON file
        with open('tickets_summary.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        print("Data successfully written to 'tickets_summary.json'.")
    else:
        print("Failed to retrieve data.")
