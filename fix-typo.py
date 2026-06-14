import re
import base64

with open('.github/workflows/build-iso.yml', 'r', encoding='utf-8') as f:
    yaml = f.read()

# Find the base64 string
match = re.search(r'echo "([A-Za-z0-9+/=]+)" \| base64 -di \| sudo -E python3', yaml)
if match:
    b64_str = match.group(1)
    decoded = base64.b64decode(b64_str).decode('utf-8')
    decoded = decoded.replace('import subprocesn', 'import subprocess')
    new_b64 = base64.b64encode(decoded.encode('utf-8')).decode('utf-8')
    yaml = yaml.replace(b64_str, new_b64)
    with open('.github/workflows/build-iso.yml', 'w', encoding='utf-8') as f:
        f.write(yaml)
    print("Fixed subprocesn!")
else:
    print("Could not find the base64 string!")
