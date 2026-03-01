with open('backend/app/services/reflection.py', 'r') as f:
    content = f.read()

content = content.replace('"turn_complete": True', '"turn_complete": False')

with open('backend/app/services/reflection.py', 'w') as f:
    f.write(content)
