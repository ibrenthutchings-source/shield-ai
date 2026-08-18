import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.agents import privacy_agent
s = 'Send to valid@example.com and leave not-an-email@com.plain'
print('OUT:', privacy_agent.redact(s))

def broken_slm(s):
    raise RuntimeError('SLM failure')

print('SANITIZE OUT:', privacy_agent.sanitize_with_slm('Contact: valid@example.com', slm_call=broken_slm))
