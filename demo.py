"""
demo.py
Apr 2025 PJW

Demonstrate methods for using SQL.
"""

import sqlite3 
import pandas as pd
import os

demo_name = 'demo.db'

#
#  Remove an old demo database if it exists
#

if os.path.exists(demo_name):
    os.remove(demo_name)

#
#  Connect to the output database
#

con = sqlite3.connect(demo_name)

#%%
#
#  Create a table using single SQL commands in a "with" block
#  to manage the context. The effect of the "with" block is to bundle
#  the commands into a single transaction.
#
#  Triple-quoted strings are very handy for splitting long SQL statements
#  across multiple lines.
#

with con:

    cur = con.execute("DROP TABLE IF EXISTS courses;")
    
    create_table = """ 
        CREATE TABLE courses (
            prefix VARCHAR,
            number INT,
            name VARCHAR,
            PRIMARY KEY (prefix,number)
            );
        """

    cur = con.execute(create_table)

#%%

#  Now add a couple of rows individually

with con:
    cur = con.execute(
        """INSERT INTO courses 
               VALUES ('pai',789,'Advanced Policy Analysis');
               """)
    cur = con.execute(
        """INSERT INTO courses 
               VALUES ('pai',723,'Economics for Public Decisions');
               """)

#%%
#
#  Define a function for printing a rowset
#

def show_rows(rows:list):
    print('\nRows:')
    for i,row in enumerate(rows):
        print(f'Row {i}',row)

#
#  Get and print the records in the table
# 

cur = con.execute("SELECT * FROM courses ORDER BY prefix,number;")
rows = cur.fetchall()
show_rows(rows)

#%%
#
#  Add more rows with one call
#

rows = [
    ('pst',101,'Intro to Analysis of Public Policy'),
    ('pai',305,'Policy Implementation'),
    ('pai',721,'Intro to Statistics'),
    ('pai',722,'Quantitative Analysis'),
    ]

with con:
    cur = con.executemany(
        "INSERT INTO courses VALUES (?,?,?);",
        rows)
    print('\nRows affected',cur.rowcount)

#
#  What's there now?
#

cur = con.execute("SELECT * FROM courses;")
show_rows(cur.fetchall())
    
#%%
#
#  Column names can be obtained from a cursor description
#

cur_info = cur.description

print('\nCursor description:')
for t,c in enumerate(cur_info):
    print(f'Tuple {t}:',c)

cols = [c[0] for c in cur_info]
print('\nColumn names:',cols)

#%%
#
#  Count the rows by prefix. Add an alias for the count.
#

cur = con.execute(
    """SELECT prefix,count(*) AS count 
           FROM courses GROUP BY prefix;""")

show_rows(cur.fetchall())
    
#%%
#
# What happens if we try to add duplicate data? Note one is new, one is old
#

rows = [
    ('pai',338,'US Intelligence Community'),
    ('pai',722,'Quantitative Analysis'),
    ]

with con:
    cur = con.executemany("INSERT INTO courses VALUES (?,?,?);",rows)
    print('\nRows affected',cur.rowcount)

#%%
#
#  What's in the database now? Neither 338 nor 722 were saved since
#  they were part of a single transaction.
#

cur = con.execute("SELECT * FROM courses ORDER BY prefix,number;")
show_rows(cur.fetchall())

#%%
#
#  Updating records
#

with con:
    cur = con.execute(
        """UPDATE courses SET name=REPLACE(name,'Intro ','Introduction ')
               WHERE name LIKE 'Intro %';
               """)

    print('\nRows affected',cur.rowcount)
        
cur = con.execute("SELECT * FROM courses ORDER BY prefix,number;")
show_rows(cur.fetchall())

#%%
#
#  Creating a second table using a SQL script
#

sql = """
    DROP TABLE IF EXISTS semesters;
    CREATE TABLE semesters (
            term INT PRIMARY KEY,
            year INT,
            name VARCHAR
            );
    INSERT INTO semesters VALUES (1242,2024,'Spring');
    INSERT INTO semesters VALUES (1251,2024,'Fall');
    INSERT INTO semesters VALUES (1252,2025,'Spring');
    INSERT INTO semesters VALUES (1261,2025,'Fall');
    """

with con:
    cur = con.executescript(sql)

cur = con.execute("SELECT * FROM semesters ORDER BY term;")
show_rows(cur.fetchall())

#%%
#
#  Create a third table for enrollments
#

with con:
    cur = con.executescript(
        """
        DROP TABLE IF EXISTS enrollment;
        CREATE TABLE enrollment (
                prefix VARCHAR,
                number INT,
                sec VARCHAR,
                term INT,
                count INT,
                UNIQUE (prefix,number,sec,term)
                );
        """)
        
    rows = [
        ('pst',101,'M001',1242,96),
        ('pst',101,'M001',1251,158),
        ('pst',101,'M001',1252,140),
        ('pai',722,'M001',1242,32),
        ('pai',722,'M002',1242,35),
        ('pai',722,'M005',1242,25),
        ('pai',789,'M001',1242,31),
        ('pai',789,'M001',1252,35),
        ]
    
    cur = con.executemany("INSERT INTO enrollment VALUES (?,?,?,?,?)",rows)

cur = con.execute("SELECT * FROM enrollment ORDER BY term,prefix,number;")
show_rows(cur.fetchall())

#%%

cur = con.executescript(
    """
    DROP VIEW IF EXISTS summary;
    CREATE VIEW summary AS
        SELECT E.prefix, E.number, E.sec, E.term, CONCAT(S.name, ' ', S.year) AS term_desc, C.name, E.count
            FROM enrollment AS E 
            JOIN semesters AS S ON E.term = S.term
            JOIN courses as C ON E.prefix = C.prefix AND E.number = C.number
    """)

cur = con.execute("SELECT * FROM summary;")
show_rows(cur.fetchall())

#%%

cur = con.execute(
    """
    SELECT * FROM summary
        WHERE prefix='pai' AND term LIKE '124%'
    """)

show_rows(cur.fetchall())
        
#%%

summary = pd.read_sql("SELECT * FROM summary",con)
print(summary)

#%%

cols = ['prefix','number','sec','term','count']

data = [['pst',101,'M001',1231,131],
        ['pst',101,'M001',1232,87] ]

df = pd.DataFrame(columns=cols,data=data)

print(df)

n = df.to_sql('enrollment',con,if_exists='append',index=False)

print("Rows affected:",n)

cur = con.execute("SELECT * FROM enrollment;")
show_rows(cur.fetchall())

con.close()

#%%

sql_tables = "SELECT * FROM sqlite_master;"

tables = pd.read_sql(sql_tables,con)

print(tables)

