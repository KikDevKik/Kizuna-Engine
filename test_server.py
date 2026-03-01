import subprocess
import time

print("Starting backend server...")
backend = subprocess.Popen(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd="backend", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(10)
print("Checking backend logs...")
for _ in range(50):
    line = backend.stdout.readline()
    if not line: break
    print(line.decode().strip())
backend.terminate()
print("Killed backend")
