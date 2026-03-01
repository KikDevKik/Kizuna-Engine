import subprocess
import time
import urllib.request
import os

print("Starting backend server...")
env = os.environ.copy()
env["GEMINI_API_KEY"] = "mock_key_for_testing"
env["MOCK_GEMINI"] = "true"

backend = subprocess.Popen(["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd="backend", env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(10)

print('Checking health...')
try:
    req = urllib.request.Request('http://localhost:8000/api/health')
    with urllib.request.urlopen(req) as response:
        print('Health check response:', response.status, response.read().decode())
except Exception as e:
    print('Health check failed:', e)

backend.terminate()
time.sleep(2)
logs, _ = backend.communicate()
print("Checking for errors in logs:")
has_error = False
for line in logs.decode().split('\n'):
    if 'ERROR' in line or 'Exception' in line or 'Traceback' in line:
        print(line)
        has_error = True

if not has_error:
    print("No startup errors found in logs!")
