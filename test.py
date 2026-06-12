import requests

ENDPOINT = "https://endpoint-f589c7dc-0c18-4bf3-b983-eeb41ccdcd01.agentbase-runtime.aiplatform.vngcloud.vn"

def ask_agent(message: str, user_id: str, session_id: str):
    response = requests.post(
        f"{ENDPOINT}/invocations",
        headers={
            "Content-Type": "application/json",
            "X-GreenNode-AgentBase-User-Id": user_id,
            "X-GreenNode-AgentBase-Session-Id": session_id,
        },
        json={"message": message}
    )
    return response.json()["response"]

# Ví dụ
print(ask_agent(
    message="viết cho tôi code c++ đơn giản",
    user_id="developer-1",
    session_id="debug-session-001"  # cùng session → agent nhớ context
))