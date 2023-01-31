import sqlite3


class DataBase:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    @classmethod
    def create_connection(cls, path):
        connection = None
        try:
            connection = sqlite3.connect(path)
        except Exception as e:
            return "Error: " + e

        return cls(connection)

    def read_query(self, query):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Exception as e:
            return "An error occurred {e}".format(e=e)

    def execute_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            return "An error occurred {e}".format(e=e)
