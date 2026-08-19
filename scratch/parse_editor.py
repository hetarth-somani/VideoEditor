import re

with open('templates/editor.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find:
# 1. Navbar and everything before container
pre_container = content[:content.find('<div class="container">')]

# 2. Extract prompt-section
prompt_match = re.search(r'(<div class="prompt-section">.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>)', content, re.DOTALL)
if not prompt_match:
    # Try broader search
    prompt_match = re.search(r'<div class="prompt-section">.*?</div>\s*</div>\s*</div>', content, re.DOTALL)

print('Prompt match found:', bool(prompt_match))

# Let's find script part
script_start = content.find('<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js">')
print('Script start index:', script_start)

# Feature buttons
buttons_match = re.search(r'<div class="feature-buttons">(.*?)</div>\s*<!-- Feature Contents -->', content, re.DOTALL)
print('Buttons match found:', bool(buttons_match))
