"""
CLARIO Security & Secret Scanner for Pre-Git Verification
Scans all tracked files for potential leaked secrets, credentials, API keys, and sensitive files.
"""
import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    'venv',
    '.pytest_cache',
    '__pycache__',
    '.git',
    'instance',
    'uploads'
}

SECRET_PATTERNS = [
    ('Gemini / Google API Key', re.compile(r'AIza[0-9A-Za-z-_]{35}')),
    ('Generic High Entropy Secret', re.compile(r'(?i)(api[_-]?key|secret[_-]?key|client[_-]?secret|password|auth_token)\s*[:=]\s*["\']([^"\']{16,})["\']')),
    ('Private Key', re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----')),
    ('PayPal Secret', re.compile(r'(?i)paypal[_-]secret\s*[:=]\s*["\']([a-zA-Z0-9_-]{20,})["\']')),
    ('Live Gemini Key in .env', re.compile(r'Ab8RN6Ki')),
]

# Whitelist allowed placeholder or test fixture patterns
WHITELIST = [
    'clario-dev-secret-key-change-in-production-2026',
    'your-secure-random-secret-key-here',
    'your_gemini_api_key_here',
    'your_paypal_sandbox_client_id',
    'your_paypal_sandbox_client_secret',
    'your_paypal_webhook_id',
    'sb-client-id-sample',
    'sb-secret-sample',
    'Password123!',
    'Admin123!',
    'INVALID_TEST_KEY_THAT_WILL_FAIL',
]

def scan_codebase():
    findings = []
    scanned_files = 0
    
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(ROOT_DIR)
            
            # Skip binary and known excluded files
            if file.endswith(('.pyc', '.db', '.sqlite', '.sqlite3', '.png', '.jpg', '.jpeg', '.pdf', '.docx', '.csv', '.ico')):
                continue
            if file == '.env':
                continue # .env is excluded by .gitignore
                
            scanned_files += 1
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                continue
                
            for name, pattern in SECRET_PATTERNS:
                matches = pattern.finditer(content)
                for m in matches:
                    matched_str = m.group(0)
                    # Check if matched string contains any whitelisted placeholder
                    if any(w in matched_str for w in WHITELIST):
                        continue
                    # Also skip this script itself
                    if 'tests/secret_scanner.py' in str(rel_path).replace('\\', '/'):
                        continue
                    line_no = content[:m.start()].count('\n') + 1
                    findings.append({
                        'type': name,
                        'file': str(rel_path),
                        'line': line_no,
                        'snippet': matched_str[:80]
                    })
                    
    return scanned_files, findings

if __name__ == '__main__':
    scanned, findings = scan_codebase()
    print(f"Scanned {scanned} files across repository.")
    if findings:
        print(f"WARNING: Found {len(findings)} potential secret leaks:")
        for f in findings:
            print(f"  [{f['type']}] in {f['file']}:{f['line']} -> {f['snippet']}")
    else:
        print("SUCCESS: 0 hardcoded secrets found across all scanned repository files!")
