import os
import json
import random
from datetime import datetime, timedelta

# Parameters
NUM_PAIRS = 10  # Number of data+optimization pairs to generate
BASE_TIMESTAMP = datetime.now()  # Starting point
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'input')

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper functions
def random_edges():
    return [f"edge{random.randint(1, 50)}" for _ in range(random.randint(1, 3))]

def random_vehicle_stats():
    return {
        "motorcycle": random.randint(0, 20),
        "car": random.randint(10, 80),
        "bus": random.randint(0, 5),
        "truck": random.randint(0, 10)
    }

def random_category(congestion):
    if congestion < 30:
        return "none"
    elif congestion < 70:
        return "mild"
    else:
        return "severe"

# Main generation loop
for i in range(NUM_PAIRS):
    timestamp = BASE_TIMESTAMP + timedelta(minutes=i)
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S-03")
    traffic_light_id = f"TL_{random.randint(0, 12)}"
    edges = random_edges()

    # Data JSON
    data_json = {
        "version": "1.0",
        "type": "data",
        "timestamp": timestamp_str,
        "traffic_light_id": traffic_light_id,
        "controlled_edges": edges,
        "metrics": {
            "vehicles_per_minute": random.randint(10, 100),
            "avg_speed_kmh": round(random.uniform(10.0, 60.0), 1),
            "avg_circulation_time_sec": random.randint(30, 180),
            "density": round(random.uniform(0.0, 1.0), 2)
        },
        "vehicle_stats": random_vehicle_stats()
    }

    # Optimization JSON
    original_congestion = random.randint(0, 100)
    optimized_congestion = random.randint(0, original_congestion)
    optimization_json = {
        "version": "1.0",
        "type": "optimization",
        "timestamp": timestamp_str,
        "traffic_light_id": traffic_light_id,
        "optimization": {
            "green_time_sec": random.randint(10, 90),
            "red_time_sec": random.randint(10, 90)
        },
        "impact": {
            "original_congestion": original_congestion,
            "optimized_congestion": optimized_congestion,
            "original_category": random_category(original_congestion),
            "optimized_category": random_category(optimized_congestion)
        }
    }

    # Save files
    data_filename = os.path.join(OUTPUT_DIR, f"data_{timestamp.strftime('%Y%m%d_%H%M%S')}.json")
    optimization_filename = os.path.join(OUTPUT_DIR, f"optimization_{timestamp.strftime('%Y%m%d_%H%M%S')}.json")

    with open(data_filename, 'w') as f:
        json.dump(data_json, f, indent=2)

    with open(optimization_filename, 'w') as f:
        json.dump(optimization_json, f, indent=2)

print(f"\n{NUM_PAIRS} data+optimization JSON pairs generated in '{OUTPUT_DIR}/'!")
