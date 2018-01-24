import os
import sqlite3


class DBManager:

    def __init__(self, db_path="data/fullpless.db", init_script="db.sql"):
        db_file_exists = os.path.exists(db_path)
        self._db = sqlite3.connect(db_path)
        if not db_file_exists:
            self.__init_db(init_script)

    def __init_db(self, sql_script):
        cursor = self._db.cursor()

        with open(sql_script, 'r') as sql_file:
            cursor.executescript(sql_file.read())

        cursor.close()
        self._db.commit()

    def get_last_id(self, table):
        query = "SELECT id FROM %s ORDER BY id DESC LIMIT 1" % table

        cursor = self._db.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        return results[0][0]

    def insert(self, table, **kwargs):
        query = "INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(kwargs.keys()), ", ".join(["?" for _ in range(len(kwargs.keys()))]))
        values = [kwargs[key] for key in kwargs.keys()]

        cursor = self._db.cursor()
        cursor.execute(query, values)
        cursor.close()
        self._db.commit()

    def update(self, table, row_id, **kwargs):
        query = "UPDATE %s SET %s WHERE id = ?" % (table, ", ".join(["%s = ?" % key for key in kwargs.keys()]))
        values = [kwargs[key] for key in kwargs.keys()] + [row_id]

        cursor = self._db.cursor()
        cursor.execute(query, values)
        cursor.close()
        self._db.commit()

    def select(self, table, **kwargs):
        query = "SELECT * FROM %s%s" % (table, " WHERE %s" % " AND ".join(["%s = ?" % x for x in kwargs.keys()]) if len(kwargs.keys()) > 0 else "")
        parameters = [kwargs[key] for key in kwargs.keys()]

        cursor = self._db.cursor()
        cursor.execute(query, parameters)
        results = cursor.fetchall()
        cursor.close()

        return results

    def delete(self, table, **kwargs):
        query = "DELETE FROM %s%s" % (table, " WHERE %s" % " AND ".join(["%s = ?" % x for x in kwargs.keys()]) if len(kwargs.keys()) > 0 else "")
        parameters = [kwargs[key] for key in kwargs.keys()]

        cursor = self._db.cursor()
        cursor.execute(query, parameters)
        cursor.close()
        self._db.commit()

    def close(self):
        self._db.commit()
        self._db.close()
