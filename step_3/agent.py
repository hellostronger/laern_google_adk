# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json

# @title Import necessary libraries
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm  # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types  # For creating message Content/Parts
from typing import Optional
from google.adk.tools.tool_context import ToolContext

# Use one of the model constants defined earlier

model = LiteLlm(
    model="openai/Qwen/Qwen2.5-7B-Instruct",  # 请替换为实际的模型名，例如 "deepseek/deepseek-chat"
    api_key = "sk-kmrvqsmsnygnmtjroupkrbfxmnuicytuwfjisklidhoqogld",  # 这里可能需要替换为实际的参数名，如 `api_key`
    base_url = "https://api.siliconflow.cn/v1",  # 硅基流动的API端点:cite[1]:cite[2]:cite[6]
)

def get_weather_stateful(city: str, tool_context: ToolContext) -> dict:
    """检索天气，根据会话状态转换温度单位。"""
    """检索天气，根据会话状态转换温度单位。"""
    # --- 参数兼容处理 ---
    if isinstance(city, str):
        # 有时模型返回整个 JSON 字符串 {"city": "New York"}
        try:
            parsed = json.loads(city)
            # 如果解析结果是 dict，就取内部 city 字段
            if isinstance(parsed, dict) and "city" in parsed:
                city = parsed["city"]
        except json.JSONDecodeError:
            # 正常的纯字符串，比如 "London" 或 "New York"
            pass
    elif isinstance(city, dict) and "city" in city:
        city = city["city"]
    print(f"--- 工具：get_weather_stateful 被调用，城市：{city} ---")

    # --- 从状态读取偏好 ---
    preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius") # 默认为摄氏度
    print(f"--- 工具：读取状态 'user_preference_temperature_unit'：{preferred_unit} ---")

    city_normalized = city.lower().replace(" ", "")

    # 模拟天气数据（内部始终以摄氏度存储）
    mock_weather_db = {
        "newyork": {"temp_c": 25, "condition": "sunny"},
        "london": {"temp_c": 15, "condition": "cloudy"},
        "tokyo": {"temp_c": 18, "condition": "light rain"},
    }

    if city_normalized in mock_weather_db:
        data = mock_weather_db[city_normalized]
        temp_c = data["temp_c"]
        condition = data["condition"]

        # 根据状态偏好格式化温度
        if preferred_unit == "Fahrenheit":
            temp_value = (temp_c * 9/5) + 32 # 计算华氏度
            temp_unit = "°F"
        else: # 默认为摄氏度
            temp_value = temp_c
            temp_unit = "°C"

        report = f"{city.capitalize()} 的天气是 {condition}，温度为 {temp_value:.0f}{temp_unit}。"
        result = {"status": "success", "report": report}
        print(f"--- 工具：以 {preferred_unit} 生成报告。结果：{result} ---")

        # 写入状态的示例（此工具可选）
        tool_context.state["last_city_checked_stateful"] = city
        print(f"--- 工具：更新状态 'last_city_checked_stateful'：{city} ---")

        return result
    else:
        # 处理未找到的城市
        error_msg = f"抱歉，我没有 '{city}' 的天气信息。"
        print(f"--- 工具：未找到城市 '{city}'。---")
        return {"status": "error", "error_message": error_msg}

print("✅ 已定义状态感知的 'get_weather_stateful' 工具。")

# @title Define the get_weather Tool
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {city} ---")  # Log tool execution
    city_normalized = city.lower().replace(" ", "")  # Basic normalization

    # Mock weather data
    mock_weather_db = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "tokyo": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."}


def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name (str, optional): The name of the person to greet. Defaults to a generic greeting if not provided.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        greeting = f"Hello, {name}!"
        print(f"--- Tool: say_hello called with name: {name} ---")
    else:
        greeting = "Hello there!"  # Default greeting if name is None or not explicitly passed
        print(f"--- Tool: say_hello called without a specific name (name_arg_value: {name}) ---")
    return greeting


def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    print(f"--- Tool: say_goodbye called ---")
    return "Goodbye! Have a great day."


print("Greeting and Farewell tools defined.")

# --- Greeting Agent ---
greeting_agent = None
try:
    greeting_agent = Agent(
        # Using a potentially different/cheaper model for a simple task
        model=model,
        # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
        name="greeting_agent",
        instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting to the user. "
                    "Use the 'say_hello' tool to generate the greeting. "
                    "If the user provides their name, make sure to pass it to the tool. "
                    "Do not engage in any other conversation or tasks.",
        description="Handles simple greetings and hellos using the 'say_hello' tool.",  # Crucial for delegation
        tools=[say_hello],
    )
    print(f"✅ Agent '{greeting_agent.name}' created using model '{greeting_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Greeting agent. Check API Key ({greeting_agent.model}). Error: {e}")

# --- Farewell Agent ---
farewell_agent = None
try:
    farewell_agent = Agent(
        # Can use the same or a different model
        model=model,
        # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
        name="farewell_agent",
        instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message. "
                    "Use the 'say_goodbye' tool when the user indicates they are leaving or ending the conversation "
                    "(e.g., using words like 'bye', 'goodbye', 'thanks bye', 'see you'). "
                    "Do not perform any other actions.",
        description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",  # Crucial for delegation
        tools=[say_goodbye],
    )
    print(f"✅ Agent '{farewell_agent.name}' created using model '{farewell_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Farewell agent. Check API Key ({farewell_agent.model}). Error: {e}")

root_agent = Agent(
    name="weather_agent_v2",  # Give it a new version name
    model=model,
    description="The main coordinator agent. Handles weather requests and delegates greetings/farewells to specialists.",
    instruction="You are the main Weather Agent coordinating a team. Your primary responsibility is to provide weather information. "
                "Use the 'get_weather' tool ONLY for specific weather requests (e.g., 'weather in London'). "
                "You have specialized sub-agents: "
                "1. 'greeting_agent': Handles simple greetings like 'Hi', 'Hello'. Delegate to it for these. "
                "2. 'farewell_agent': Handles simple farewells like 'Bye', 'See you'. Delegate to it for these. "
                "Analyze the user's query. If it's a greeting, delegate to 'greeting_agent'. If it's a farewell, delegate to 'farewell_agent'. "
                "If it's a weather request, handle it yourself using 'get_weather'. "
                "For anything else, respond appropriately or state you cannot handle it."
                "you must return appropriate args according to schema,or you will be killed",

    tools=[get_weather],  # Root agent still needs the weather tool for its core task
    # Key change: Link the sub-agents here!
    sub_agents=[greeting_agent, farewell_agent]
)

# Sample queries to test the agent:

# # Agent will give weather information for the specified cities.
# # What's the weather in Tokyo?
# # What is the weather like in London?
# # Tell me the weather in New York?

# # Agent will not have information for the specified city.
# # How about Paris?

# # Agent will delegate greetings to the greeting_agent.
# # Hi there!
# # Hello!
# # Hello,  this is alice

# # Agent will delegate farewells to the farewell_agent.
# # Bye!
# # See you later!
# # Thanks, bye!