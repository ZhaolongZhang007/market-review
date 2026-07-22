#!/usr/bin/env bash
# 每日盘后复盘一条龙。收盘后（15:00 之后）运行：  ./daily.sh
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"   # 没建 venv 就退回系统 python

echo "──────────────────────────────────────────"
echo "  A股盘后复盘 · $(date '+%Y-%m-%d %H:%M')"
echo "──────────────────────────────────────────"

echo
echo "① 抓取当日数据（东财慢，约 2-5 分钟，请耐心等）…"
$PY update_data.py

echo
echo "② 生成提示词并复制到剪贴板…"
$PY make_prompt.py

echo
echo "──────────────────────────────────────────"
echo "  现在去 chat（claude.ai / chatgpt.com）："
echo "    1. Cmd+V 把提示词发出去"
echo "    2. 等它输出 JSON，全选复制它的回复"
echo "    3. 复制好后，回到这里按 [回车] 继续"
echo "──────────────────────────────────────────"
read -r -p "  复制好模型回复后按回车…"

echo
echo "③ 解析并写入 insights.json…"
$PY save_insights.py

echo
echo "──────────────────────────────────────────"
echo "  完成。打开页面查看："
echo "    $PY -m http.server 8000   → http://localhost:8000/"
echo "──────────────────────────────────────────"
