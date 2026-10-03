import psycopg2
import os
from dotenv import load_dotenev
def getConnection():
    return psycopg2.connect(
        host="localhost",
        dbname="ontime",
        user="postgres",
        password=os.environ["DB_PASSWORD"],
        port = 5432
    )

def createTable():
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delay(
    id serial primary key, 
    trip_id VARCHAR not null, 
    stop_id VARCHAR NOT NULL,
    route_id VARCHAR NOT NULL,
    delay_seconds INTEGER NOT NULL,
    scheduled_ts TIMESTAMP NOT NULL,
    actual_ts TIMESTAMP NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
    )""")
    conn.commit()
    cursor.close()
    conn.close()

def insert(data):
    conn = getConnection()
    cursor = conn.cursor()
    for i in data:
        cursor.execute(
            """
            INSERT INTO delay(trip_id,stop_id,route_id,delay_seconds,scheduled_ts,actual_ts) VALUES (%s,%s,%s,%s,to_timestamp(%s),to_timestamp(%s))""",
            (i["trip_id"],i["stop_id"],i["route_id"],i["delay_seconds"],i["scheduled_ts"],i["actual_ts"])
    )
    conn.commit()
    cursor.close()
    conn.close()

def getAverage():
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute("SELECT stop_id, route_id, AVG(delay_seconds) FROM delay GROUP BY stop_id, route_id")
    rows = cursor.fetchall()
    avg = {}
    for i in rows:
        avg[(i[0], i[1])] = i[2]
    cursor.close()
    conn.close()
    return avg