with open('backend/tests/test_vision_flow.py', 'r') as f:
    content = f.read()

content = "import pytest\n" + content
with open('backend/tests/test_vision_flow.py', 'w') as f:
    f.write(content)
