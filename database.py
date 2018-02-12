"""
Database utils

Created by Tony Liu (388848@163.com)
Date: 02/11/2018
"""
import sqlite3
import re


def getDatabaseConnection():
    def regexp(y, x, search=re.search):
        return 1 if search(y, x) else 0
    conn = sqlite3.connect("numbers.db")
    conn.create_function('regexp', 2, regexp)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tbl_numbers
    (
        number VARCHAR(11) NOT NULL PRIMARY KEY,
        tag VARCHAR(255) DEFAULT "",
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    return conn
