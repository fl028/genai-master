import xml.etree.ElementTree as ET
from lxml import etree
import logging
import requests
import json
import mysql.connector
from mysql.connector import Error, IntegrityError
import time

class Api:
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'd': 'http://schemas.microsoft.com/ado/2007/08/dataservices',
        'm': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata',
        'error': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'
    }

    def __init__(self, config):
        self.user = config.get('api-user')
        self.password = config.get('api-password')
        self.path = config.get('api-url')
        self.__set_basic_auth()
        self.__set_header()

    def __set_basic_auth(self):
        self.session = requests.Session()
        self.session.auth = (self.user, self.password)

    def __set_header(self):
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.headers.update({"X-Requested-With": "X"})

    def __retrun_html_error(self, response):
        root = ET.fromstring(response.content)
        message = self._get_text(root.find('error:message', self.namespaces))

        raise Exception(f"Statuscode: {str(response.status_code)} Content: '{message}' ")

    def _get_text(self,element):
        return element.text.strip() if element is not None and element.text else None

    def read(self, ticket_id):
        request_path = self.path.replace("<ID>",str(ticket_id))
        response = self.session.get(request_path)

        if response.status_code == 200:
            parser = etree.XMLParser(recover=True)
            root = etree.fromstring(response.content, parser=parser)

            parsed_data = {
                'id': self._get_text(root.find('atom:id', self.namespaces)),
                'title': self._get_text(root.find('atom:title', self.namespaces)),
                'updated': self._get_text(root.find('atom:updated', self.namespaces)),
                'category': {
                    'scheme': root.find('atom:category', self.namespaces).attrib.get('scheme'),
                    'term': root.find('atom:category', self.namespaces).attrib.get('term')
                },
                'links': [
                    {
                        'href': link.attrib.get('href'),
                        'rel': link.attrib.get('rel'),
                        'title': link.attrib.get('title'),
                        'type': link.attrib.get('type')
                    }
                    for link in root.findall('atom:link', self.namespaces)
                ],
                'properties': {
                    'sap_ticketstatus': self._get_text(root.find('atom:content/m:properties/d:sap_ticketstatus', self.namespaces)),
                    'sap_ticketstatus_t': self._get_text(root.find('atom:content/m:properties/d:sap_ticketstatus_t', self.namespaces)),
                    'sap_ticketno': self._get_text(root.find('atom:content/m:properties/d:sap_ticketno', self.namespaces)),
                    'cdl_text': self._get_text(root.find('atom:content/m:properties/d:cdl_text', self.namespaces)),
                    'id': self._get_text(root.find('atom:content/m:properties/d:id', self.namespaces)),
                    'guid': self._get_text(root.find('atom:content/m:properties/d:guid', self.namespaces)),
                    'processtype': self._get_text(root.find('atom:content/m:properties/d:processtype', self.namespaces)),
                    'action': self._get_text(root.find('atom:content/m:properties/d:action', self.namespaces)),
                    'company': self._get_text(root.find('atom:content/m:properties/d:company', self.namespaces)),
                    'reporter': self._get_text(root.find('atom:content/m:properties/d:reporter', self.namespaces)),
                    'supportteam': self._get_text(root.find('atom:content/m:properties/d:supportteam', self.namespaces)),
                    'editor': self._get_text(root.find('atom:content/m:properties/d:editor', self.namespaces)),
                    'status': self._get_text(root.find('atom:content/m:properties/d:status', self.namespaces)),
                    'statustxt': self._get_text(root.find('atom:content/m:properties/d:statustxt', self.namespaces)),
                    'category': self._get_text(root.find('atom:content/m:properties/d:category', self.namespaces)),
                    'component': self._get_text(root.find('atom:content/m:properties/d:component', self.namespaces)),
                    'ibase': self._get_text(root.find('atom:content/m:properties/d:ibase', self.namespaces)),
                    'sysrole': self._get_text(root.find('atom:content/m:properties/d:sysrole', self.namespaces)),
                    'priority': self._get_text(root.find('atom:content/m:properties/d:priority', self.namespaces)),
                    'title': self._get_text(root.find('atom:content/m:properties/d:title', self.namespaces)),
                    'text': self._get_text(root.find('atom:content/m:properties/d:text', self.namespaces)),
                    'text2': self._get_text(root.find('atom:content/m:properties/d:text2', self.namespaces)),
                    'security': self._get_text(root.find('atom:content/m:properties/d:security', self.namespaces)),
                    'postpuntil': self._get_text(root.find('atom:content/m:properties/d:postpuntil', self.namespaces)),
                    'linkid': self._get_text(root.find('atom:content/m:properties/d:linkid', self.namespaces)),
                    'cdlid': self._get_text(root.find('atom:content/m:properties/d:cdlid', self.namespaces)),
                    'optid': self._get_text(root.find('atom:content/m:properties/d:optid', self.namespaces)),
                    'psp': self._get_text(root.find('atom:content/m:properties/d:psp', self.namespaces)),
                    'units': self._get_text(root.find('atom:content/m:properties/d:units', self.namespaces)),
                    'type': self._get_text(root.find('atom:content/m:properties/d:type', self.namespaces)),
                }
            }
            return parsed_data
        else:
           self.__retrun_html_error(response)

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

        
    def insert_ticket(self, properties):
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor()

                # Insert query
                insert_query = """
                INSERT INTO tickets (
                    id, sap_ticketstatus, sap_ticketstatus_t, sap_ticketno, cdl_text, guid,
                    processtype, action, company, reporter, supportteam, editor,
                    status, statustxt, category, component, ibase, sysrole,
                    priority, title, text, text2, security, postpuntil,
                    linkid, cdlid, optid, psp, units, type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                # Tuple of values to insert
                values = (
                    properties['id'], properties['sap_ticketstatus'], properties['sap_ticketstatus_t'], properties['sap_ticketno'],
                    properties['cdl_text'], properties['guid'], properties['processtype'], properties['action'], properties['company'],
                    properties['reporter'], properties['supportteam'], properties['editor'], properties['status'], properties['statustxt'],
                    properties['category'], properties['component'], properties['ibase'], properties['sysrole'], properties['priority'],
                    properties['title'], properties['text'], properties['text2'], properties['security'], properties['postpuntil'],
                    properties['linkid'], properties['cdlid'], properties['optid'], properties['psp'], properties['units'], properties['type']
                )

                # Execute the query
                cursor.execute(insert_query, values)
                self.connection.commit()

                print("Ticket inserted successfully")
            else:
                print("Failed to connect to the database.")
        except IntegrityError as e:
            if 'PRIMARY' in e.msg:
                print(f"Ticket already exists: {e.msg}")
        except Error as e:
            print(f"Error: {e}")
        finally:
            if self.connection.is_connected():
                cursor.close()
                #self.connection.close()
                #print("MySQL connection is closed")

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  

    # Read configuration file
    with open('config.json', 'r') as file:
        config = json.load(file)

    ticket_id = 11851846 # 01.06.2024
    steps = 1

    #create connection
    api = Api(config)
    db = DB(config)

    for i in range(steps):
        # check db
        ticket_exists = db.check_ticket_exists_in_db(ticket_id)

        if not ticket_exists:
            print(f"Process: {ticket_id}")
            #read
            try:
                parsed_data = api.read(ticket_id)
                #print(parsed_data)
                db.insert_ticket(parsed_data['properties'])
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(1)
        else:
            print("Skipping ...")

        ticket_id = ticket_id - 1
