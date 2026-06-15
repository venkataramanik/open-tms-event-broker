import time
import json
import pika
import psycopg2

def connect_db():
    while True:
        try:
            conn = psycopg2.connect(
                host="postgres",
                database="tms_ledger",
                user="postgres",
                password="pure_opensource_secret"
            )
            return conn
        except psycopg2.OperationalError:
            print("Waiting for relational database engine...")
            time.sleep(3)

def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tms_audit_trail (
            id SERIAL PRIMARY KEY,
            event_id VARCHAR(50) UNIQUE NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            facility_id VARCHAR(50) NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_payload JSONB
        );
    """)
    conn.commit()
    cursor.close()

def process_message(ch, method, properties, body):
    print(f" [x] Processing Carrier Event: {body.decode()}")
    event_data = json.loads(body.decode())
    
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tms_audit_trail (event_id, event_type, facility_id, raw_payload)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING;
            """,
            (event_data['event_id'], event_data['event_type'], event_data['facility_id'], json.dumps(event_data['payload']))
        )
        conn.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(" [✓] Event committed cleanly to open data ledger.")
    except Exception as e:
        print(f" [!] Data persistence failure: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        cursor.close()
        conn.close()

def main():
    conn = connect_db()
    init_db(conn)
    conn.close()

    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()
            channel.queue_declare(queue='tms_events', durable=True)
            break
        except Exception:
            print("Waiting for message broker...")
            time.sleep(3)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='tms_events', on_message_callback=process_message)
    print(' [*] Background tracking daemon initialized.')
    channel.start_consuming()

if __name__ == '__main__':
    main()
