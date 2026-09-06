"""
Script to generate demo data for the recommendation system.
"""
import json
import random
import time
from datetime import datetime, timedelta
from confluent_kafka import Producer

# Kafka configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'demo-data-producer'
}

producer = Producer(conf)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def generate_event():
    """Generate a demo e-commerce event."""
    event_types = ['view', 'click', 'purchase']
    product_ids = [f'product_{i}' for i in range(1, 101)]  # 100 products
    user_ids = [f'user_{i}' for i in range(1, 101)]      # 100 users for demo

    event_type = random.choice(event_types)
    product_id = random.choice(product_ids)
    user_id = random.choice(user_ids)
    timestamp = int(time.time())

    # For purchase, add quantity and price
    if event_type == 'purchase':
        quantity = random.randint(1, 5)
        price = round(random.uniform(10.0, 500.0), 2)
        event = {
            'event_type': event_type,
            'product_id': product_id,
            'user_id': user_id,
            'timestamp': timestamp,
            'quantity': quantity,
            'price': price
        }
    else:
        event = {
            'event_type': event_type,
            'product_id': product_id,
            'user_id': user_id,
            'timestamp': timestamp
        }

    return event

def main():
    topic = 'ecommerce_events'
    print(f'Generating demo events to topic: {topic}')

    # Generate 1000 events
    for i in range(1000):
        event = generate_event()
        producer.produce(
            topic,
            key=event['user_id'],
            value=json.dumps(event),
            callback=delivery_report
        )
        producer.poll(0)
        time.sleep(0.01)  # Generate events quickly

    producer.flush()
    print('Demo data generation complete.')

if __name__ == '__main__':
    main()