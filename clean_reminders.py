import asyncio
import aiosqlite

async def clean():
    async with aiosqlite.connect("./data/voice_agent.db") as db:
        cursor = await db.execute("SELECT id, message, trigger_time, status FROM reminders")
        rows = await cursor.fetchall()
        print("Current reminders:")
        for r in rows:
            print(f"  ID={r[0]} | time={r[2]} | status={r[3]} | msg={r[1][:50]}")

        # Cancel ALL old/stale reminders
        await db.execute("UPDATE reminders SET status='cancelled' WHERE status='active'")
        await db.commit()
        print("\nAll old active reminders cancelled. Fresh start.")

asyncio.run(clean())
