from app.services.security_scanner_service import scan_content

sample = '''
import requests

API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"
DB_PASSWORD = "SuperSecret123!"

def fetch(url):
    return requests.get(url, verify=False)

def run_cmd(cmd):
    os.system(cmd)

eval(user_input)
'''

findings = scan_content("app/example.py", sample)
for f in findings:
    print(f"[{f.severity.upper()}] {f.title} (line {f.line_number}): {f.matched_snippet}")
    