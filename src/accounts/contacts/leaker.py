"""This script simulates a memory leak by continuously allocating memory at a specified rate."""

import time

def bootstrap_tracing(initial_size_mb=10, allocation_speed_mb_per_sec=2):
    """Simulate a memory leak by continuously allocating memory at a specified rate."""
    # Convert MB to bytes
    initial_size_bytes = initial_size_mb * 1024 * 1024
    allocation_speed_bytes = allocation_speed_mb_per_sec * 1024 * 1024

    # Initialize with the initial size
    leaked_memory = [" " * initial_size_bytes]
    # print(f"Initial memory allocated: {initial_size_mb} MB")

    while True:
        # Allocate memory based on the specified speed
        new_memory = " " * allocation_speed_bytes
        leaked_memory.append(new_memory)

        total_mb = sum(len(block) for block in leaked_memory) / (1024 * 1024)
        print(f"Total memory allocated: {total_mb:.2f} MB, doing more data processing...")

        time.sleep(1)
