import subprocess
import time
import requests

print("Starting backend server...")
backend = subprocess.Popen(["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd="backend", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(15)

print("Checking health...")
try:
    r = requests.get("http://localhost:8000/api/health")
    print("Health check response:", r.status_code, r.text)
except Exception as e:
    print("Health check failed:", e)

print("Checking backend logs...")
backend.terminate()
time.sleep(2)
logs, _ = backend.communicate()
for line in logs.decode().split('\n'):
    if "ERROR" in line or "Exception" in line or "Traceback" in line:
        print(line)
print("Finished checking backend logs.")
