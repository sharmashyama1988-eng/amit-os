import os
import time
import shutil
import subprocess

def get_memory_usage():
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_total = 0
        mem_available = 0
        
        for line in lines:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1])
                
        if mem_total > 0:
            mem_used = mem_total - mem_available
            return (mem_used / mem_total) * 100
    except Exception as e:
        print(f"Error reading memory info: {e}")
    return 0

def clear_directory(path):
    if not os.path.exists(path):
        return
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception as e:
            print(f"Failed to delete {item_path}. Reason: {e}")

def optimize():
    print("Running optimization...")
    
    # Clear temporary files
    clear_directory('/tmp')
    clear_directory('/var/cache/apt/archives')
    
    # Check memory usage
    mem_usage = get_memory_usage()
    print(f"Current memory usage: {mem_usage:.2f}%")
    
    if mem_usage > 90:
        print("Memory usage above 90%, dropping caches...")
        try:
            # Drop caches
            subprocess.run(['sync'], check=True)
            with open('/proc/sys/vm/drop_caches', 'w') as f:
                f.write('3\n')
            print("Caches dropped successfully.")
        except Exception as e:
            print(f"Failed to drop caches: {e}")

if __name__ == "__main__":
    while True:
        optimize()
        time.sleep(3600) # Sleep for 1 hour
