import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv(
    "AGENT_ENDPOINT",
    "https://endpoint-f589c7dc-0c18-4bf3-b983-eeb41ccdcd01.agentbase-runtime.aiplatform.vngcloud.vn",
)
USER_ID = os.getenv("CHAT_USER_ID", "developer-1")


def ask(message: str, session_id: str) -> str:
    try:
        resp = requests.post(
            f"{ENDPOINT}/invocations",
            headers={
                "Content-Type": "application/json",
                "X-GreenNode-AgentBase-User-Id": USER_ID,
                "X-GreenNode-AgentBase-Session-Id": session_id,
            },
            json={"message": message},
            timeout=120,
        )
        data = resp.json()
        if data.get("status") == "success":
            return data["response"]
        return f"[Lỗi] {data.get('error', resp.text)}"
    except requests.Timeout:
        return "[Lỗi] Agent timeout sau 120 giây."
    except Exception as e:
        return f"[Lỗi] Không kết nối được: {e}"


def main():
    session_id = str(uuid.uuid4())
    print(f"\nCode & Log Analyst — gõ 'exit' để thoát, 'new' để tạo session mới")
    print(f"Session: {session_id[:8]}...\n")

    while True:
        try:
            user_input = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoát.")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Thoát.")
            break
        if user_input.lower() == "new":
            session_id = str(uuid.uuid4())
            print(f"Session mới: {session_id[:8]}...\n")
            continue

        print("Agent: ", end="", flush=True)
        response = ask(user_input, session_id)
        print(response)
        print()


if __name__ == "__main__":
    main()
