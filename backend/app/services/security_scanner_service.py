"""
Scans repository files for hardcoded secrets and risky code patterns
using regex-based detection. No AI calls — fast, deterministic, free.
"""
import re
from dataclasses import dataclass


@dataclass
class Finding:
    severity: str       # "critical" | "high" | "medium" | "low"
    category: str
    title: str
    description: str
    line_number: int | None
    matched_snippet: str | None


# ── Secret detection patterns ───────────────────────────────────────
# Each tuple: (compiled regex, severity, category, title, description)
SECRET_PATTERNS = [
    (
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "critical", "hardcoded_secret", "AWS Access Key ID",
        "A hardcoded AWS Access Key ID was found. AWS keys should never be committed to source control.",
    ),
    (
        re.compile(r"(?i)aws(.{0,20})?(secret|access)?[_-]?key(.{0,20})?[\"']\s*[:=]\s*[\"'][A-Za-z0-9/+=]{40}[\"']"),
        "critical", "hardcoded_secret", "AWS Secret Access Key",
        "A hardcoded AWS Secret Access Key was found.",
    ),
    (
        re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA|PGP) PRIVATE KEY-----"),
        "critical", "hardcoded_secret", "Private Key",
        "A private key file was found embedded in source code.",
    ),
    (
        re.compile(r"(?i)(api[_-]?key|apikey)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']"),
        "high", "hardcoded_secret", "Hardcoded API Key",
        "A hardcoded API key was found. Move this to an environment variable.",
    ),
    (
        re.compile(r"(?i)(secret[_-]?key|secret_token|client_secret)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']"),
        "high", "hardcoded_secret", "Hardcoded Secret Key",
        "A hardcoded secret/token was found. Move this to an environment variable.",
    ),
    (
        re.compile(r"(?i)password[\"']?\s*[:=]\s*[\"'][^\"'\s]{6,}[\"']"),
        "high", "hardcoded_secret", "Hardcoded Password",
        "A hardcoded password was found in source code.",
    ),
    (
        re.compile(r"(?i)(bearer|authorization)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-\.]{20,}[\"']"),
        "high", "hardcoded_secret", "Hardcoded Auth Token",
        "A hardcoded bearer token or authorization header value was found.",
    ),
    (
        re.compile(r"ghp_[A-Za-z0-9]{36}"),
        "critical", "hardcoded_secret", "GitHub Personal Access Token",
        "A GitHub personal access token was found hardcoded in source.",
    ),
    (
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        "critical", "hardcoded_secret", "OpenAI-style API Key",
        "An OpenAI-style secret key (sk-...) was found hardcoded in source.",
    ),
    (
        re.compile(r"mongodb(\+srv)?://[^\s\"']+:[^\s\"']+@"),
        "critical", "hardcoded_secret", "MongoDB Connection String with Credentials",
        "A MongoDB connection string containing embedded credentials was found.",
    ),
    (
        re.compile(r"postgres(ql)?://[^\s\"']+:[^\s\"']+@"),
        "critical", "hardcoded_secret", "PostgreSQL Connection String with Credentials",
        "A PostgreSQL connection string containing embedded credentials was found.",
    ),
]

# ── Risky code pattern detection ────────────────────────────────────
RISKY_PATTERNS = [
    (
        re.compile(r"\beval\s*\("),
        "medium", "risky_pattern", "Use of eval()",
        "eval() executes arbitrary code and is a common injection vector. Avoid if possible.",
    ),
    (
        re.compile(r"\bexec\s*\("),
        "medium", "risky_pattern", "Use of exec()",
        "exec() executes arbitrary code and is a common injection vector. Avoid if possible.",
    ),
    (
        re.compile(r"subprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True"),
        "high", "risky_pattern", "Shell Injection Risk",
        "subprocess call with shell=True can be vulnerable to shell injection if input is not sanitized.",
    ),
    (
        re.compile(r"os\.system\s*\("),
        "medium", "risky_pattern", "Use of os.system()",
        "os.system() passes input to the shell and can be vulnerable to injection. Prefer subprocess with a list of args.",
    ),
    (
        re.compile(r"pickle\.loads?\s*\("),
        "medium", "risky_pattern", "Unsafe Deserialization (pickle)",
        "Deserializing untrusted data with pickle can lead to arbitrary code execution.",
    ),
    (
        re.compile(r"(?i)(execute|executemany)\s*\(\s*[\"'].*%s.*[\"']\s*%"),
        "high", "risky_pattern", "Possible SQL Injection",
        "SQL query built via string formatting instead of parameterized queries — potential SQL injection risk.",
    ),
    (
        re.compile(r"(?i)(execute|executemany)\s*\(\s*f[\"']"),
        "high", "risky_pattern", "Possible SQL Injection (f-string)",
        "SQL query built via an f-string instead of parameterized queries — potential SQL injection risk.",
    ),
    (
        re.compile(r"verify\s*=\s*False"),
        "medium", "risky_pattern", "SSL Verification Disabled",
        "SSL certificate verification is disabled, exposing the app to man-in-the-middle attacks.",
    ),
    (
        re.compile(r"debug\s*=\s*True"),
        "low", "risky_pattern", "Debug Mode Enabled",
        "Debug mode appears to be hardcoded to True — should be disabled in production.",
    ),
]

ALL_PATTERNS = SECRET_PATTERNS + RISKY_PATTERNS

# Skip binary/asset/lockfile types — no point scanning these, and they can be huge
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".whl", ".pyc", ".so", ".dll", ".exe",
    ".lock",
}


def _should_skip(path: str) -> bool:
    lower = path.lower()
    return any(lower.endswith(ext) for ext in SKIP_EXTENSIONS)


def scan_content(path: str, content: str) -> list[Finding]:
    """
    Scans a single file's content and returns all findings.
    """
    if _should_skip(path) or not content:
        return []

    findings: list[Finding] = []
    lines = content.splitlines()

    for pattern, severity, category, title, description in ALL_PATTERNS:
        for match in pattern.finditer(content):
            # Figure out which line the match falls on
            line_number = content[: match.start()].count("\n") + 1
            snippet = lines[line_number - 1].strip() if 0 < line_number <= len(lines) else match.group(0)

            # Truncate snippet to avoid storing huge lines (e.g. minified files)
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."

            findings.append(
                Finding(
                    severity=severity,
                    category=category,
                    title=title,
                    description=description,
                    line_number=line_number,
                    matched_snippet=snippet,
                )
            )

    return findings