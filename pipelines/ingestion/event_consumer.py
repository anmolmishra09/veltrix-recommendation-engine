"""
Kafka consumer for reading e-commerce events and storing them in a data lake.
"""
import json
import os
from datetime import datetime
from confluent_kafka import Consumer, KafkaError

# Kafka configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'ecommerce-event-consumer-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)

# Data lake directory (simulating S3/minio)
DATA_LAKE_PATH = './data_lake'
os.makedirs(DATA_LAKE_PATH, exist_ok=True)

def main():
    topic = 'ecommerce_events'
    consumer.subscribe([topic])

    print(f'Consuming events from topic: {topic}')

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            event = json.loads(msg.value().decode('utf-8'))
            # Store event in data lake partitioned by date
            event_date = datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d')
            partition_path = os.path.join(DATA_LAKE_PATH, event_date)
            os.makedirs(partition_path, exist_ok=True)

            # Write event as JSON line
            file_path = os.path.join(partition_path, f"events_{datetime.now().strftime('%H%M%S')}.json")
            with open(file_path, 'a') as f:
                f.write(json.dumps(event) + '\n')

            print(f'Stored event: {event["event_type"]} by {event["user_id"]} for {event["product_id"]}')

    except KeyboardInterrupt:
        print('Interrupted')
    finally:
        consumer.close()

if __name__ == '__main__':
    main()