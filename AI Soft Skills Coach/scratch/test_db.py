import asyncio
from src.db.db_config import Sessionlocal
from sqlalchemy import text

async def test_conn():
    try:
        async with Sessionlocal() as session:
            # Query conversations
            res = await session.execute(text("SELECT id, user_id, topic, status, created_at FROM conversations WHERE user_id = 2"))
            convs = res.all()
            print("Conversations for Test User:", convs)
            
            # Query messages
            res_msgs = await session.execute(text("SELECT id, conversation_id, sender, message_text FROM messages LIMIT 20"))
            msgs = res_msgs.all()
            print("Recent messages in database:", msgs)
    except Exception as e:
        print("DB Connection Error:", e)

if __name__ == "__main__":
    asyncio.run(test_conn())
