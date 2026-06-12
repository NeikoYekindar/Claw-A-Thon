# Hướng dẫn Deploy Agent `code-log-analyst`

Agent chuyên phân tích code và log, chạy trên GreenNode AgentBase (Custom Agent — Docker image).

---

## Thông tin dự án

| Thông tin | Giá trị |
|-----------|---------|
| Tên agent | `code-log-analyst` |
| Runtime ID | `runtime-9bc71c24-35df-414b-aaac-895c8cf6a000` |
| Memory ID | `memory-c94b9e7c-0c4b-48ae-8528-de87718b48aa` |
| Container Registry | `vcr.vngcloud.vn/111480-abp111815` |
| Image tag | `vcr.vngcloud.vn/111480-abp111815/code-log-analyst:latest` |
| LLM Model | `qwen/qwen3-5-27b` |
| Agent Endpoint | `https://endpoint-f589c7dc-0c18-4bf3-b983-eeb41ccdcd01.agentbase-runtime.aiplatform.vngcloud.vn` |

---

## Yêu cầu công cụ

Trước khi chạy lệnh, phải có đủ các công cụ sau:

| Công cụ | Kiểm tra |
|---------|----------|
| Git Bash | Mở **Git Bash** (không phải CMD hay PowerShell) |
| Docker Desktop | Phải **đang chạy** (icon ở system tray) |
| jq | Đã cài qua winget |

---

## Bước 0 — Chuẩn bị môi trường (mỗi lần mở Git Bash mới)

Chạy hai lệnh này ở đầu mỗi session Git Bash:

```bash
# Thêm jq vào PATH
export PATH="$PATH:/c/Users/LAP15273/AppData/Local/Microsoft/WinGet/Packages/jqlang.jq_Microsoft.Winget.Source_8wekyb3d8bbwe"

# Thêm Docker vào PATH
export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"
```

> **Tip:** Có thể thêm 2 dòng này vào file `~/.bashrc` để không phải gõ lại mỗi lần.

---

## Bước 1 — Thay đổi code (nếu cần)

Sửa file trong thư mục `vngdc-claw-a-thon/`:

- **Logic agent**: [main.py](main.py) — sửa `system_prompt`, thêm tools, thay đổi logic xử lý
- **Thư viện**: [requirements.txt](requirements.txt) — thêm package mới
- **Cấu hình container**: [Dockerfile](Dockerfile) — thay đổi base image, cổng,...

---

## Bước 2 — Đăng nhập vào Container Registry

Chạy từ thư mục `vngdc-claw-a-thon/`:

```bash
SCRIPTS="../greennode-agentbase-skills/.claude/skills/agentbase/scripts"

bash "$SCRIPTS/cr.sh" credentials docker-login
```

Kết quả thành công:
```
Login Succeeded
```

> Lệnh này tự lấy credentials từ `.greennode.json` và đăng nhập Docker — không cần nhập password thủ công.

---

## Bước 3 — Build Docker image

Chạy từ thư mục `vngdc-claw-a-thon/`:

```bash
docker build -t vcr.vngcloud.vn/111480-abp111815/code-log-analyst:latest .
```

Quá trình build mất khoảng 2-5 phút lần đầu (tải base image), các lần sau nhanh hơn nhờ Docker cache.

Kiểm tra image đã build:
```bash
docker images | grep code-log-analyst
```

---

## Bước 4 — Push image lên Container Registry

```bash
docker push vcr.vngcloud.vn/111480-abp111815/code-log-analyst:latest
```

Kết quả thành công sẽ có dòng `latest: digest: sha256:...`.

---

## Bước 5 — Update runtime trên GreenNode

```bash
SCRIPTS="../greennode-agentbase-skills/.claude/skills/agentbase/scripts"

bash "$SCRIPTS/runtime.sh" update runtime-9bc71c24-35df-414b-aaac-895c8cf6a000 \
  --image vcr.vngcloud.vn/111480-abp111815/code-log-analyst:latest \
  --flavor runtime-s2-general-2x4 \
  --from-cr \
  --env-file .env
```

GreenNode sẽ tạo một version mới và bắt đầu rolling update.

---

## Bước 6 — Theo dõi trạng thái deploy

```bash
SCRIPTS="../greennode-agentbase-skills/.claude/skills/agentbase/scripts"

bash "$SCRIPTS/runtime.sh" get runtime-9bc71c24-35df-414b-aaac-895c8cf6a000
```

Chờ đến khi `status` chuyển từ `UPDATING` → `ACTIVE`.

Có thể poll tự động:
```bash
while true; do
  STATUS=$(bash "$SCRIPTS/runtime.sh" get runtime-9bc71c24-35df-414b-aaac-895c8cf6a000 \
    | grep '"status"' | head -1 | cut -d'"' -f4)
  echo "$(date '+%H:%M:%S') — Status: $STATUS"
  [ "$STATUS" = "ACTIVE" ] && echo "Deploy thành công!" && break
  sleep 10
done
```

---

## Bước 7 — Test agent sau khi deploy

### Dùng Python (file `test.py`)

```bash
cd vngdc-claw-a-thon
python test.py
```

### Dùng curl trực tiếp

```bash
curl -s -X POST \
  https://endpoint-f589c7dc-0c18-4bf3-b983-eeb41ccdcd01.agentbase-runtime.aiplatform.vngcloud.vn/invocations \
  -H "Content-Type: application/json" \
  -H "X-GreenNode-AgentBase-User-Id: test-user" \
  -H "X-GreenNode-AgentBase-Session-Id: test-session-001" \
  -d '{"message": "Phân tích lỗi: NullPointerException at line 42 in UserService.java"}' \
  | python -m json.tool
```

### Kiểm tra health

```bash
curl https://endpoint-f589c7dc-0c18-4bf3-b983-eeb41ccdcd01.agentbase-runtime.aiplatform.vngcloud.vn/health
```

---

## Tóm tắt quy trình redeploy

```
Sửa code  →  docker build  →  docker push  →  runtime update  →  chờ ACTIVE  →  test
```

```bash
SCRIPTS="../greennode-agentbase-skills/.claude/skills/agentbase/scripts"

# 1. Login registry
bash "$SCRIPTS/cr.sh" credentials docker-login

# 2. Build
docker build -t vcr.vngcloud.vn/111480-abp111815/code-log-analyst:latest .

# 3. Push
docker push vcr.vngcloud.vn/111480-abp111815/code-log-analyst:latest

# 4. Update runtime
bash "$SCRIPTS/runtime.sh" update runtime-9bc71c24-35df-414b-aaac-895c8cf6a000 \
  --image vcr.vngcloud.vn/111480-abp111815/code-log-analyst:latest \
  --flavor runtime-s2-general-2x4 \
  --from-cr \
  --env-file .env

# 5. Kiểm tra status
bash "$SCRIPTS/runtime.sh" get runtime-9bc71c24-35df-414b-aaac-895c8cf6a000
```

---

## Xử lý lỗi thường gặp

### `docker: command not found`
→ Chưa thêm Docker vào PATH. Chạy lại Bước 0.

### `jq: command not found`
→ Chưa thêm jq vào PATH. Chạy lại Bước 0.

### `unauthorized: authentication required` khi push
→ Chạy lại `cr.sh credentials docker-login` (token hết hạn).

### `Error response from daemon: context canceled` khi build
→ Docker Desktop bị tắt. Mở lại và chờ icon ở system tray chuyển sang trạng thái running.

### Runtime vẫn `UPDATING` sau 10 phút
→ Có thể build lỗi trong container. Kiểm tra logs:
```bash
bash "$SCRIPTS/runtime.sh" logs runtime-9bc71c24-35df-414b-aaac-895c8cf6a000
```

### Agent trả về lỗi `MEMORY_ID not set`
→ File `.env` thiếu `MEMORY_ID`. Giá trị đúng: `memory-c94b9e7c-0c4b-48ae-8528-de87718b48aa`

---

## Cấu trúc file

```
vngdc-claw-a-thon/
├── main.py              ← Code chính của agent
├── requirements.txt     ← Python dependencies
├── Dockerfile           ← Cấu hình Docker image
├── .env                 ← Secrets (KHÔNG commit lên git)
├── .env.example         ← Template cho .env
├── .dockerignore        ← Loại trừ file nhạy cảm khỏi image
├── .greennode.json      ← IAM credentials (KHÔNG commit lên git)
├── .agentbase-state.json← Trạng thái deploy hiện tại
├── test.py              ← Script test agent
└── DEPLOY.md            ← File hướng dẫn này
```
