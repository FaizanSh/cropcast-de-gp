from kafka import KafkaProducer
import json
import random
import time

# Set static values for soil_quality_index and farm_size_hectares (generated once)
soil_quality_index = random.randint(1, 10) # static
farm_size_hectares = round(random.uniform(200, 1000), 2) # static

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],  # Change this if needed
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Define feature ranges
feature_ranges = {
    'rainfall': (0, 500),
    'fertilizer': (1, 5),
    'sunlight_hours': (0, 9),
}

def generate_event():
    event = {
        'rainfall': random.uniform(*feature_ranges['rainfall']),
        'soil_quality_index': soil_quality_index,
        'farm_size_hectares': farm_size_hectares,
        'sunlight_hours': random.uniform(*feature_ranges['sunlight_hours']),
        'fertilizer': random.randint(*feature_ranges['fertilizer'])
    }
    return event

# Send data to Kafka
topic_name = 'farm_predictions'

while True:
    data = generate_event()
    print(f"Sending: {data}")
    producer.send(topic_name, value=data)
    time.sleep(5)  # Adjust frequency as needed
