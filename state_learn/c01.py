# @title 1. 初始化新会话服务和状态

# 导入必要的会话组件
from google.adk.sessions import InMemorySessionService
import asyncio
async def myfun():
    APP_NAME = "bjq"
    # 为此状态演示创建新的会话服务实例
    session_service_stateful = InMemorySessionService()
    print("✅ 已为状态演示创建新的 InMemorySessionService。")

    # 为教程的这一部分定义新的会话 ID
    SESSION_ID_STATEFUL = "session_state_demo_001"
    USER_ID_STATEFUL = "user_state_demo"

    # 定义初始状态数据 - 用户最初偏好摄氏度
    initial_state = {
        "user_preference_temperature_unit": "Celsius"
    }

    # 创建会话，提供初始状态
    session_stateful = await session_service_stateful.create_session(
        app_name=APP_NAME, # 使用一致的应用名称
        user_id=USER_ID_STATEFUL,
        session_id=SESSION_ID_STATEFUL,
        state=initial_state # <<< 在创建期间初始化状态
    )
    print(f"✅ 已为用户 '{USER_ID_STATEFUL}' 创建会话 '{SESSION_ID_STATEFUL}'。")

    # 验证初始状态是否正确设置
    retrieved_session = await session_service_stateful.get_session(app_name=APP_NAME,
                                                             user_id=USER_ID_STATEFUL,
                                                             session_id = SESSION_ID_STATEFUL)
    print("\n--- 初始会话状态 ---")
    if retrieved_session:
        print(retrieved_session.state)
    else:
        print("错误：无法检索会话。")
if __name__ == '__main__':
    asyncio.run(myfun())