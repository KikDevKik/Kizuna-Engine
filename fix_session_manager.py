with open('backend/app/services/session_manager.py', 'r') as f:
    content = f.read()

import re

# Remove The Babel Protocol block
pattern = r"# 🏰 BASTION: The Babel Protocol \(Phase 7\.5\).*?system_instruction \+= f\"\\n\\n\[CRITICAL DIRECTIVE\]: The user's system language is \{lang\}\. You MUST ALWAYS speak and respond fluently in \{lang\}, maintaining your established personality\.\""

content = re.sub(pattern, "", content, flags=re.DOTALL)

with open('backend/app/services/session_manager.py', 'w') as f:
    f.write(content)
