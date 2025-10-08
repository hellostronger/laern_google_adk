# @title 1. 初始化新会话服务和状态
import asyncio
# 导入必要的会话组件
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm

from step_3.agent import say_hello, say_goodbye, get_weather_stateful

model = LiteLlm(
    model="openai/Qwen/Qwen2.5-7B-Instruct",  # 请替换为实际的模型名，例如 "deepseek/deepseek-chat"
    api_key = "sk-kmrvqsmsnygnmtjroupkrbfxmnuicytuwfjisklidhoqogld",  # 这里可能需要替换为实际的参数名，如 `api_key`
    base_url = "https://api.siliconflow.cn/v1",  # 硅基流动的API端点:cite[1]:cite[2]:cite[6]
)

async def  myfun():
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

    # @title 3. Redefine Sub-Agents and Update Root Agent with output_key

    # Ensure necessary imports: Agent, LiteLlm, Runner
    from google.adk.agents import Agent
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.runners import Runner
    # Ensure tools 'say_hello', 'say_goodbye' are defined (from Step 3)
    # Ensure model constants MODEL_GPT_4O, MODEL_GEMINI_2_5_PRO etc. are defined

    # --- Redefine Greeting Agent (from Step 3) ---
    greeting_agent = None
    try:
        greeting_agent = Agent(
            model=model,
            name="greeting_agent",
            instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting using the 'say_hello' tool. Do nothing else.",
            description="Handles simple greetings and hellos using the 'say_hello' tool.",
            tools=[say_hello],
        )
        print(f"✅ Agent '{greeting_agent.name}' redefined.")
    except Exception as e:
        print(f"❌ Could not redefine Greeting agent. Error: {e}")

    # --- Redefine Farewell Agent (from Step 3) ---
    farewell_agent = None
    try:
        farewell_agent = Agent(
            model=model,
            name="farewell_agent",
            instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message using the 'say_goodbye' tool. Do not perform any other actions.",
            description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
            tools=[say_goodbye],
        )
        print(f"✅ Agent '{farewell_agent.name}' redefined.")
    except Exception as e:
        print(f"❌ Could not redefine Farewell agent. Error: {e}")

    # --- Define the Updated Root Agent ---
    root_agent_stateful = None
    runner_root_stateful = None  # Initialize runner

    # Check prerequisites before creating the root agent
    if greeting_agent and farewell_agent and 'get_weather_stateful' in globals():

        root_agent_model = model  # Choose orchestration model

        root_agent_stateful = Agent(
            name="weather_agent_v4_stateful",  # New version name
            model=root_agent_model,
            description="Main agent: Provides weather (state-aware unit), delegates greetings/farewells, saves report to state.",
            instruction="You are the main Weather Agent. Your job is to provide weather using 'get_weather_stateful'. "
                        "The tool will format the temperature based on user preference stored in state. "
                        "Delegate simple greetings to 'greeting_agent' and farewells to 'farewell_agent'. "
                        "Handle only weather requests, greetings, and farewells.",
            tools=[get_weather_stateful],  # Use the state-aware tool
            sub_agents=[greeting_agent, farewell_agent],  # Include sub-agents
            output_key="last_weather_report"  # <<< Auto-save agent's final weather response
        )
        print(f"✅ Root Agent '{root_agent_stateful.name}' created using stateful tool and output_key.")

        # --- Create Runner for this Root Agent & NEW Session Service ---
        runner_root_stateful = Runner(
            agent=root_agent_stateful,
            app_name=APP_NAME,
            session_service=session_service_stateful  # Use the NEW stateful session service
        )
        print(
            f"✅ Runner created for stateful root agent '{runner_root_stateful.agent.name}' using stateful session service.")

    else:
        print("❌ Cannot create stateful root agent. Prerequisites missing.")
        if not greeting_agent: print(" - greeting_agent definition missing.")
        if not farewell_agent: print(" - farewell_agent definition missing.")
        if 'get_weather_stateful' not in globals(): print(" - get_weather_stateful tool missing.")
if __name__ == '__main__':
    asyncio.run(myfun())
