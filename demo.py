"""
demo.py
Apr 2025 PJW

Demonstrate methods for using SQL.
"""

import sqlite3 
import pandas as pd
import os
import sys

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
#  Table will have a two-column primary key consisting of the prefix 
#  and number. They uniquely identify the course.
#

with con:

    cur = con.execute("DROP TABLE IF EXISTS courses;")
    
    create_table = """ 
        CREATE TABLE courses (
            prefix VARCHAR,
            number INT,
            name VARCHAR,
            PRIMARY KEY (prefix,number) ); 
        """

    cur = con.execute(create_table)

#%%
#
#  Now add a couple of rows individually
#

insert_one = """
    INSERT INTO courses 
        VALUES ('pai',789,'Advanced Policy Analysis'); 
    """

insert_two = """
    INSERT INTO courses 
        VALUES ('pai',723,'Economics for Public Decisions'); 
    """

with con:
    cur = con.execute(insert_one)
    cur = con.execute(insert_two)

#%%
#
#  Define a function for printing a rowset
#

def show_rows(rows:list) -> None:
    print('\nRows:')
    for i,row in enumerate(rows):
        print(f'Row {i}',row)

#
#  Get and print the records in the table
# 

cur = con.execute("SELECT * FROM courses;")
rows = cur.fetchall()
show_rows(rows)

#%%
#
#  Selecting with sorting
# 

cur = con.execute("SELECT * FROM courses ORDER BY prefix,number;")
show_rows(cur.fetchall())

#%%
#
#  Add several rows with one call
#

rows = [
    ('pst',101,'Intro to Analysis of Public Policy'),
    ('pai',305,'Policy Implementation'),
    ('pai',721,'Intro to Statistics'),
    ('pai',722,'Quantitative Analysis'),
    ]

with con:
    cur = con.executemany("INSERT INTO courses VALUES (?,?,?);",rows)
    print('\nRows affected',cur.rowcount)

#
#  What's there now?
#

cur = con.execute("SELECT * FROM courses;") 
show_rows(cur.fetchall())
    
#%%
#
#  Column names can be obtained from a cursor description. The description
#  is a tuple of tuples: one for each column. The first element of each 
#  tuple is the column name and the remainder are None (extra elements are
#  for compatibility with another standard Python module).
#

cur_info = cur.description

print('\nCursor description:')
for t,c in enumerate(cur_info):
    print(f'Tuple {t}:',c)

cols = [c[0] for c in cur_info]
print('\nColumn names:',cols)

#
#  Define a function for easy printing later
#

def show_cols(cur: sqlite3.Cursor) -> None:
    print('\nColumn names:',[c[0] for c in cur.description])

#%%
#
#  Count the rows by prefix. Add an alias for the count.
#

count_recs = """
    SELECT prefix,count(*) AS count 
        FROM courses GROUP BY prefix;
    """

cur = con.execute(count_recs)
show_rows(cur.fetchall())
show_cols(cur)
    
#%%
#
#  What happens if we try to add duplicate data? Expect an IntegrityError.
#  Note 338 is new but 722 is old
#

rows = [
    ('pai',338,'US Intelligence Community'),
    ('pai',722,'Another Quantitative Analysis'),
    ]

with con:
    cur = con.executemany("INSERT INTO courses VALUES (?,?,?);",rows)
    print('\nRows affected',cur.rowcount)

#%%
#
#  What's in the database now? Neither 338 nor 722 were saved since
#  they were part of a single transaction.
#

cur = con.execute("SELECT * FROM courses;")
show_rows(cur.fetchall())

#%%
#
#  Updating records
#

update_cmd = """
    UPDATE courses SET name=REPLACE(name,'Intro ','Introduction ')
        WHERE name LIKE 'Intro %';
    """

with con:
    cur = con.execute(update_cmd)
    print('\nRows affected',cur.rowcount)
        
cur = con.execute("SELECT * FROM courses ORDER BY prefix,number;")
show_rows(cur.fetchall())

#%%
#
#  Creating a second table using a SQL script (sequence of commands). USe
#  term as the primary key: there should only be one entry per term and 
#  it is the main column for linking.
#

sql_cmds = """
    DROP TABLE IF EXISTS semesters;
    
    CREATE TABLE semesters (
            term INT PRIMARY KEY,
            year INT,
            name VARCHAR
            );
    
    INSERT INTO semesters VALUES (1231,2022,'Fall');
    INSERT INTO semesters VALUES (1232,2023,'Spring');
    INSERT INTO semesters VALUES (1241,2023,'Fall');
    INSERT INTO semesters VALUES (1242,2024,'Spring');
    INSERT INTO semesters VALUES (1251,2024,'Fall');
    INSERT INTO semesters VALUES (1252,2025,'Spring');
    INSERT INTO semesters VALUES (1261,2025,'Fall');
    """

with con:
    cur = con.executescript(sql_cmds)

cur = con.execute("SELECT * FROM semesters ORDER BY term;")
show_rows(cur.fetchall())

#%%
#
#  Create a third table for enrollments and add some records
#

create_enrollment = """
    DROP TABLE IF EXISTS enrollment;
    CREATE TABLE enrollment (
        prefix VARCHAR,
        number INT,
        sec VARCHAR,
        term INT,
        count INT,
        UNIQUE (prefix,number,sec,term) );
    """

with con:
    cur = con.executescript(create_enrollment)
        
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
#
#  Create a view (virtual table) that links all three tables. The view will 
#  be stored in the database and can be used much like a table except that
#  it will be read-only: INSERTs and UPDATEs are not allowed.
#
#  Aliases are used for table names for clarity in the JOINs, and || is 
#  used to concatenate the semester name and year in a reader-friendly 
#  format. JOINS are INNER by default but can be LEFT, RIGHT, or several 
#  other options.
#
#  The AS term in the CREATE statement can be used to create new tables out 
#  of existing tables as well.
#

create_summary = """
    DROP VIEW IF EXISTS summary;
    
    CREATE VIEW summary AS
        SELECT E.prefix, E.number, E.sec, E.term, S.name || ' ' || S.year AS term_desc, C.name, E.count
            FROM enrollment AS E 
                JOIN semesters AS S ON E.term = S.term
                JOIN courses as C ON E.prefix = C.prefix AND E.number = C.number
    """

cur = con.executescript(create_summary)

cur = con.execute("SELECT * FROM summary;")
show_rows(cur.fetchall())

#%%
#
#  Selecting data from the view for a particular semester
#  

select_cmd = """
    SELECT * FROM summary
        WHERE prefix='pai' AND term LIKE '124%'
    """

cur = con.execute(select_cmd)
show_rows(cur.fetchall())
        
#%%
#
#  Counting total enrollment by class
#

count_cmd = """
    SELECT term,prefix,number,sum(count) as students FROM summary
        GROUP BY prefix,number,term
        ORDER BY term,prefix,number
    """
    
cur = con.execute(count_cmd)
show_rows(cur.fetchall())
show_cols(cur) 

#%%
#
#  Adding another enrollment record and checking the view
#

insert_789 = """
    INSERT INTO enrollment VALUES ('pai',789,'M001',1232,33);
    """

with con:
    cur = con.execute(insert_789)

cur = con.execute("SELECT * FROM summary;")
show_rows(cur.fetchall())

#%%
#
#  Now read the table using Pandas
#

summary = pd.read_sql("SELECT * FROM summary",con)
print(summary)

#%%
#
#  Build a dataframe and use it to add data to a table
#

cols = ['prefix','number','sec','term','count']

data = [['pst',101,'M001',1231,131],
        ['pst',101,'M001',1232,87] ]

df = pd.DataFrame(columns=cols,data=data)

print(df)

#
#  Call the .to_sql() method. It returns the number of rows affected
#

n = df.to_sql('enrollment',con,if_exists='append',index=False)

print("Rows affected:",n)

#
#  Show the updated table
#

cur = con.execute("SELECT * FROM enrollment;")
show_rows(cur.fetchall())

con.close()

#%%
#
#  Open an database of electricty data and print its schema. Start by checking 
#  whether the file is present
#

eia_file = 'eia860.db'

if not os.path.exists(eia_file):
    print('\nNeed to download eia860.db to run the remainder of the script')
    sys.exit()

#
#  Get information about the tables and print it
#
    
con = sqlite3.connect(eia_file)

cur = con.execute("SELECT name,sql FROM sqlite_master;")
rows = cur.fetchall()

print(f'\nSchema of {eia_file}:')

for name,sql in rows:
    print("\nTable:",name,"\n")
    print(sql)

#%%
#
#  Look up NYS generating capacity. Note backquotes around the column name
#  with spaces in it.
#

ny_gen = """
    SELECT Technology, SUM(`Nameplate Capacity (MW)`) AS mw FROM Generator
        WHERE State = 'NY'
            GROUP BY Technology
    """
    
data = pd.read_sql(ny_gen,con)

print(data)
