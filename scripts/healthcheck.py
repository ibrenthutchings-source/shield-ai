import os
import sys
import asyncio

try:
    import asyncpg
except Exception as exc:
    print("asyncpg not installed or import failed:", exc, file=sys.stderr)
    sys.exit(1)

async def check():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set", file=sys.stderr)
        return 2
    try:
        conn = await asyncio.wait_for(asyncpg.connect(dsn), timeout=5)
        await conn.close()
        return 0
    except Exception as e:
        print(f"db check failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    code = asyncio.run(check())
    sys.exit(code)
