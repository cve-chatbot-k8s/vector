import os
import psycopg2
from psycopg2 import sql


# Singleton class to connect to PostgreSQL DB
class PostgresConnector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PostgresConnector, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Ensure __init__ is run only once
            self.host = os.getenv('DB_HOST')
            self.port = os.getenv('DB_PORT')
            self.database = os.getenv('DB_NAME')
            self.user = os.getenv('DB_USER')
            self.password = os.getenv('DB_PASSWORD')
            self.connection = None
            self.initialized = True

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print("Connection to PostgreSQL DB successful")
        except Exception as e:
            print(f"Error: {e}")
            self.connection = None

    def close(self):
        if self.connection:
            self.connection.close()
            print("PostgreSQL connection closed")
