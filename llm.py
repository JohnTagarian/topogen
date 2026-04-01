import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from prompts import STAGE1_SYSTEM, STAGE1_USER, STAGE2_SYSTEM, STAGE2_USER

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            temperature=0.3,
            max_tokens=4096,
        )
    return _client


def _parse_json_response(text: str) -> dict:
    """Strip markdown fences if present, then parse JSON."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def parse_requirements(user_input: str) -> dict:
    """Stage 1: Parse natural language requirements into structured parameters."""
    client = _get_client()
    messages = [
        SystemMessage(content=STAGE1_SYSTEM),
        HumanMessage(content=STAGE1_USER.format(user_input=user_input)),
    ]
    response = client.invoke(messages)
    return _parse_json_response(response.content)


def design_topology(parsed_params: dict) -> dict:
    """Stage 2: Design network topology from structured parameters."""
    client = _get_client()
    messages = [
        SystemMessage(content=STAGE2_SYSTEM),
        HumanMessage(content=STAGE2_USER.format(
            parsed_params_json=json.dumps(parsed_params, ensure_ascii=False, indent=2)
        )),
    ]
    response = client.invoke(messages)
    return _parse_json_response(response.content)


if __name__ == "__main__":
    test_input = "ออฟฟิศ 3 ชั้น ชั้นละ 30 คน มี Server Room 1 ห้อง ต้องการ WiFi ทุกชั้น"
    print("=== Stage 1: Parse Requirements ===")
    params = parse_requirements(test_input)
    print(json.dumps(params, ensure_ascii=False, indent=2))

    print("\n=== Stage 2: Design Topology ===")
    topology = design_topology(params)
    print(json.dumps(topology, ensure_ascii=False, indent=2))
