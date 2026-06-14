import re

filepath = 'd:/Amit os/.github/workflows/build-iso.yml'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match: sudo tee "PATH" > /dev/null << 'MARKER'\nCONTENT\nMARKER
pattern = r'(sudo tee "([^"]+)" > /dev/null << \'([A-Z]+)\'\n(.*?)\n\3)'

def replacer(match):
    full_match = match.group(1)
    file_path = match.group(2)
    marker = match.group(3)
    inner_content = match.group(4)
    
    import base64
    b64_content = base64.b64encode(inner_content.encode('utf-8')).decode('utf-8')
    
    return f'echo "{b64_content}" | base64 -d | sudo tee "{file_path}" > /dev/null'

new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

# Also fix python heredoc
py_pattern = r'(python3 << \'PYEOF\'\n(.*?)\nPYEOF)'
def py_replacer(match):
    inner_content = match.group(2)
    import base64
    b64_content = base64.b64encode(inner_content.encode('utf-8')).decode('utf-8')
    return f'echo "{b64_content}" | base64 -d | python3'

new_content = re.sub(py_pattern, py_replacer, new_content, flags=re.DOTALL)

# Same for bash heredoc
bash_pattern = r'(cat << \'EOF\' > ([^\n]+)\n(.*?)\nEOF)'
def bash_replacer(match):
    file_path = match.group(2)
    inner_content = match.group(3)
    import base64
    b64_content = base64.b64encode(inner_content.encode('utf-8')).decode('utf-8')
    return f'echo "{b64_content}" | base64 -d > {file_path}'

new_content = re.sub(bash_pattern, bash_replacer, new_content, flags=re.DOTALL)


with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_content)

print(f"Replaced heredocs. Original size: {len(content)}, New size: {len(new_content)}")
