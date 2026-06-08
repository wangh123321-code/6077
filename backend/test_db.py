import asyncio
import os
import asyncpg

async def test():
    url = os.environ.get("DATABASE_URL")
    print(f"Testing connection to: {url}")
    try:
        conn = await asyncpg.connect(url)
        print("Connected!")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
