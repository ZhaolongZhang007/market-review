#!/usr/bin/env python3
"""判断今天是不是 A 股交易日，用于让定时任务跳过周末和法定节假日。

设计上**失败开放**：日历源拿不到时，退回"工作日即交易日"，宁可多跑一次
（多花约 $0.15）也不要因为新浪挂了而静默跳过每一天——后者看起来一切正常，
是最糟的失败模式。

    python3 check_trading_day.py          # 交易日 exit 0，非交易日 exit 1
    python3 check_trading_day.py --quiet  # 不打印，只用退出码

在 GitHub Actions 里会把结果写进 $GITHUB_OUTPUT 的 is_trading_day。
"""
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")


def resolve(today):
    """返回 (是否交易日, 判定依据)。"""
    # 周末永远不是交易日——这条不依赖任何外部源。
    if today.weekday() >= 5:
        return False, "周末"

    try:
        import akshare as ak
    except Exception as exc:
        return True, f"akshare 不可用（{type(exc).__name__}），按工作日处理[失败开放]"

    try:
        df = ak.tool_trade_date_hist_sina()
    except Exception as exc:
        return True, f"交易日历抓取失败（{type(exc).__name__}），按工作日处理[失败开放]"

    try:
        dates = {str(d)[:10] for d in df["trade_date"].tolist()}
    except Exception as exc:
        return True, f"交易日历字段异常（{type(exc).__name__}），按工作日处理[失败开放]"

    if not dates:
        return True, "交易日历为空，按工作日处理[失败开放]"

    key = today.strftime("%Y-%m-%d")
    if key in dates:
        return True, f"新浪交易日历确认（覆盖至 {max(dates)}）"

    # 不在日历里：可能是节假日，也可能是日历还没发布到今年。
    # 只有当日历确实覆盖到今天之后，"不在里面"才是可信的"非交易日"。
    if max(dates) >= key:
        return False, f"新浪交易日历判定为非交易日（覆盖至 {max(dates)}）"
    return True, f"交易日历仅覆盖到 {max(dates)}，未及今日，按工作日处理[失败开放]"


def main():
    quiet = "--quiet" in sys.argv
    now = datetime.now(SHANGHAI)
    is_trading, reason = resolve(now)

    if not quiet:
        label = "交易日" if is_trading else "非交易日"
        print(f"{now:%Y-%m-%d %a} (Asia/Shanghai) → {label}：{reason}")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"is_trading_day={'true' if is_trading else 'false'}\n")
            fh.write(f"reason={reason}\n")

    return 0 if is_trading else 1


if __name__ == "__main__":
    sys.exit(main())
