# database_functions.py

import psycopg2
from datetime import datetime

# Database connection parameters
db_name = 'Parking_ticket'
db_user = 'postgres'
db_password = 'Appu#369'
db_host = 'localhost'
db_port = '5432'

def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        return None
# 
def create_table():
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS number_plate_details (
        id SERIAL PRIMARY KEY,
        number_plate VARCHAR(20) NOT NULL,
        timestamp_entering TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        timestamp_leaving TIMESTAMP,
        time_taken INTERVAL,
        parking_fee NUMERIC

    )
    '''
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
            print("Table created successfully.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
        finally:
            cursor.close()
            conn.close()

def insert_entry(number_plate, timestamp_entering):
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            insert_query = '''
                INSERT INTO number_plate_details (number_plate, timestamp_entering)
                VALUES (%s, %s) RETURNING id;
            '''
            cursor.execute(insert_query, (number_plate, timestamp_entering))
            conn.commit()
            entry_id = cursor.fetchone()[0]
            return entry_id
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
        finally:
            cursor.close()
            conn.close()

def update_entry(entry_id, timestamp_leaving, time_taken, parking_fee):
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            update_query = '''
                UPDATE number_plate_details
                SET timestamp_leaving = %s, time_taken = %s, parking_fee = %s
                WHERE id = %s;
            '''
            cursor.execute(update_query, (timestamp_leaving, time_taken, parking_fee, entry_id))
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
        finally:
            cursor.close()
            conn.close()

def calculate_parking_fee(timestamp_entering, timestamp_leaving):
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = '''
                SELECT calculate_parking_fee(%s, %s)
            '''
            cursor.execute(query, (timestamp_entering, timestamp_leaving))
            parking_fee = cursor.fetchone()[0]
            return parking_fee
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
        finally:
            cursor.close()
            conn.close()


def fetch_data():
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            fetch_query = '''
                SELECT * FROM number_plate_details;
            '''
            cursor.execute(fetch_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            return df
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
        finally:
            cursor.close()
            conn.close()
    return pd.DataFrame() 