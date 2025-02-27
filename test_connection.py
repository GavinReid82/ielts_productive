# test_connection.py
import psycopg2
from psycopg2 import OperationalError
import socket
import ssl

def test_connection():
    print("DNS Lookup...")
    try:
        ip = socket.gethostbyname("ielts-productive-group.postgres.database.azure.com")
        print(f"Server IP: {ip}")
    except Exception as e:
        print(f"DNS lookup failed: {e}")

    print("\nAttempting database connection...")
    try:
        conn = psycopg2.connect(
            dbname="ielts_db",
            user="gavin",
            password="productive1$",
            host="ielts-productive-group.postgres.database.azure.com",
            port="5432",
            sslmode="require",
            connect_timeout=10
        )
        print("Connected successfully!")
        conn.close()
    except OperationalError as e:
        print(f"Connection failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_connection()