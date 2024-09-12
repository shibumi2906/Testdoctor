import sqlite3

def create_db():
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS patients
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       lastname TEXT NOT NULL,
                       firstname TEXT NOT NULL,
                       middlename TEXT NOT NULL,
                       birthdate DATE NOT NULL,
                       visit_date DATE NOT NULL)''')
    conn.commit()
    conn.close()

# Вызов функции для создания базы данных
create_db()
