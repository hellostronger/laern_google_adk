# Ensure the stateful runner (runner_root_stateful) is available from the previous cell
# Ensure call_agent_async, USER_ID_STATEFUL, SESSION_ID_STATEFUL, APP_NAME are defined

# @title Define Agent Interaction Function
import asyncio
from google.genai import types # For creating message Content/Parts
import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm # 用于多模型支持
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # 用于创建消息 Content/Parts

from step_3.agent import get_weather, say_hello, say_goodbye, get_weather_stateful

session_service_stateful = InMemorySessionService()

# 为教程的这一部分定义新的会话 ID
SESSION_ID_STATEFUL = "session_state_demo_001"
USER_ID_STATEFUL = "user_state_demo"
# --- Define the Updated Root Agent ---
root_agent_stateful = None
runner_root_stateful = None  # Initialize runner
initial_state = {
    "user_preference_temperature_unit": "Celsius"
}
APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"  # Using a fixed ID for simplicity

async def myfun():
    session_stateful = await session_service_stateful.create_session(
        app_name=APP_NAME,  # 使用一致的应用名称
        user_id=USER_ID_STATEFUL,
        session_id=SESSION_ID_STATEFUL,
        state=initial_state  # <<< 在创建期间初始化状态
    )


    # @title Setup Session Service and Runner

    # --- Session Management ---
    # Key Concept: SessionService stores conversation history & state.
    # InMemorySessionService is simple, non-persistent storage for this tutorial.
    session_service = InMemorySessionService()

    # Define constants for identifying the interaction context


    model = LiteLlm(
        model="openai/Qwen/Qwen2.5-7B-Instruct",  # 请替换为实际的模型名，例如 "deepseek/deepseek-chat"
        api_key = "sk-kmrvqsmsnygnmtjroupkrbfxmnuicytuwfjisklidhoqogld",  # 这里可能需要替换为实际的参数名，如 `api_key`
        base_url = "https://api.siliconflow.cn/v1",  # 硅基流动的API端点:cite[1]:cite[2]:cite[6]
        auto_json_loads=True
    )
    AGENT_MODEL = model # 从强大的 Gemini 模型开始

    weather_agent = Agent(
        name="weather_agent_v1",
        model=AGENT_MODEL, # 指定底层 LLM
        description="为特定城市提供天气信息。", # 对于稍后的任务分配至关重要
        instruction="你是一个有用的天气助手。你的主要目标是提供当前天气报告。"
                    "当用户询问特定城市的天气时，"
                    "你必须使用 'get_weather' 工具查找信息。"
                    "分析工具的响应：如果状态为 'error'，礼貌地告知用户错误信息。"
                    "如果状态为 'success'，向用户清晰简洁地呈现天气 'report'。"
                    "仅在提到城市进行天气请求时使用该工具。",
        tools=[get_weather], # 使该工具可用于此智能体
    )

    print(f"Agent '{weather_agent.name}' created using model '{AGENT_MODEL}'.")
    # Create the specific session where the conversation will happen
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

    # --- Runner ---
    # Key Concept: Runner orchestrates the agent execution loop.
    runner = Runner(
        agent=weather_agent, # The agent we want to run
        app_name=APP_NAME,   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    print(f"Runner created for agent '{runner.agent.name}'.")

    async def call_agent_async(query: str, runner, user_id, session_id):
        """Sends a query to the agent and prints the final response."""
        print(f"\n>>> User Query: {query}")

        content = types.Content(role='user', parts=[types.Part(text=query)])
        final_response_text = "智能体没有产生最终响应。"

        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = f"智能体升级：{event.error_message or '无特定消息。'}"
                break

        print(f"<<< Agent Response: {final_response_text}")

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
                        "Handle only weather requests, greetings, and farewells."
                        "\n\n"
        "IMPORTANT: When generating function calls to tools, ALWAYS output the 'arguments' field as a JSON object "
        "(dictionary) rather than a string. For example:\n"
        "Correct: {\"city\": \"New York\"}\n"
        "Incorrect: \"{\\\"city\\\": \\\"New York\\\"}\"\"\n"
        "This ensures that the FunctionCall args pass validation and the tool is executed properly.",
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

    if 'runner_root_stateful' in globals() and runner_root_stateful:
        async def run_stateful_conversation():
            try:
                print("\n--- Testing State: Temp Unit Conversion & output_key ---")

                # 1. Check weather (Uses initial state: Celsius)
                print("--- Turn 1: Requesting weather in London (expect Celsius) ---")
                await call_agent_async(
                    query="Hi!",
                    # query="What's the weather in London?",
                                       runner=runner_root_stateful,
                                       user_id=USER_ID_STATEFUL,
                                       session_id=SESSION_ID_STATEFUL
                                       )

                # 2. Manually update state preference to Fahrenheit - DIRECTLY MODIFY STORAGE
                print("\n--- Manually Updating State: Setting unit to Fahrenheit ---")
                # Access the internal storage directly - THIS IS SPECIFIC TO InMemorySessionService for testing
                stored_session = session_service_stateful.sessions[APP_NAME][USER_ID_STATEFUL][SESSION_ID_STATEFUL]
                stored_session.state["user_preference_temperature_unit"] = "Fahrenheit"
                # Optional: You might want to update the timestamp as well if any logic depends on it
                # import time
                # stored_session.last_update_time = time.time()
                print(
                    f"--- 已更新存储的会话状态。当前 'user_preference_temperature_unit'：{stored_session.state['user_preference_temperature_unit']} ---")
            except KeyError:
                print(
                    f"--- 错误：无法从内部存储中检索会话 '{SESSION_ID_STATEFUL}'，用户 '{USER_ID_STATEFUL}'，应用 '{APP_NAME}' 以更新状态。检查 ID 和是否创建了会话。---")
            except Exception as e:
                print(f"--- 更新内部会话状态时出错：{e} ---")

            # 3. Check weather again (Tool should now use Fahrenheit)
            # This will also update 'last_weather_report' via output_key
            print("\n--- Turn 2: Requesting weather in New York (expect Fahrenheit) ---")
            await call_agent_async("Tell me the weather in New York.",
                                   runner=runner_root_stateful,
                                   user_id=USER_ID_STATEFUL,
                                   session_id=SESSION_ID_STATEFUL
                                   )

            # 4. Test basic delegation (should still work)
            # This will update 'last_weather_report' again, overwriting the NY weather report
            print("\n--- Turn 3: Sending a greeting ---")
            await call_agent_async(query="Hi!",
                                   runner=runner_root_stateful,
                                   user_id=USER_ID_STATEFUL,
                                   session_id=SESSION_ID_STATEFUL
                                   )

        # Execute the conversation
        await run_stateful_conversation()

        # 方法 1：直接 await（笔记本/异步 REPL 的默认方式）
        # 如果你的环境支持顶级 await（如 Colab/Jupyter 笔记本），
        # # 这意味着事件循环已经在运行，所以你可以直接 await 函数。
        # print("尝试使用 'await' 执行（笔记本默认）...")
        # await run_stateful_conversation()

        # METHOD 2: asyncio.run (For Standard Python Scripts [.py])
        # If running this code as a standard Python script from your terminal,
        # the script context is synchronous. `asyncio.run()` is needed to
        # create and manage an event loop to execute your async function.
        # To use this method:
        # 1. Comment out the `await run_stateful_conversation()` line above.
        # 2. Uncomment the following block:
        """
        import asyncio
        if __name__ == "__main__": # Ensures this runs only when script is executed directly
            print("Executing using 'asyncio.run()' (for standard Python scripts)...")
            try:
                # This creates an event loop, runs your async function, and closes the loop.
                asyncio.run(run_stateful_conversation())
            except Exception as e:
                print(f"An error occurred: {e}")
        """

        # --- Inspect final session state after the conversation ---
        # This block runs after either execution method completes.
        print("\n--- Inspecting Final Session State ---")
        final_session = await session_service_stateful.get_session(app_name=APP_NAME,
                                                                   user_id=USER_ID_STATEFUL,
                                                                   session_id=SESSION_ID_STATEFUL)
        if final_session:
            # Use .get() for safer access to potentially missing keys
            print(f"Final Preference: {final_session.state.get('user_preference_temperature_unit', 'Not Set')}")
            print(
                f"Final Last Weather Report (from output_key): {final_session.state.get('last_weather_report', 'Not Set')}")
            print(
                f"Final Last City Checked (by tool): {final_session.state.get('last_city_checked_stateful', 'Not Set')}")
            # Print full state for detailed view
            # print(f"Full State Dict: {final_session.state}") # For detailed view
        else:
            print("\n❌ Error: Could not retrieve final session state.")

    else:
        print("\n⚠️ Skipping state test conversation. Stateful root agent runner ('runner_root_stateful') is not available.")

if __name__ == '__main__':
    asyncio.run(myfun())
