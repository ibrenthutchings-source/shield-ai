import os, sys
sys.path.insert(0, os.getcwd())
from email_validator import validate_email, EmailNotValidError
for addr in ["valid@example.com", "not-an-email@com.plain"]:
    try:
        info = validate_email(addr)
        print(addr, "VALID ->", info.email)
    except EmailNotValidError as e:
        print(addr, "INVALID ->", e)
