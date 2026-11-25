import os
import getpass

# 설정 정보
PROJECT_DIR = "/Users/naewon/workspace/ai_trading_bot"
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "bin", "python3")
SCRIPT_PATH = os.path.join(PROJECT_DIR, "daily_scanner.py")
USER_NAME = getpass.getuser()
PLIST_LABEL = "com.ai_trading_bot.daily_scanner"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{PLIST_LABEL}.plist")
SHELL_SCRIPT_PATH = os.path.join(PROJECT_DIR, "run_scanner.sh")
LOG_PATH = os.path.join(PROJECT_DIR, "automation.log")

# 1. 실행용 쉘 스크립트 생성
shell_content = f"""#!/bin/bash
# AI 트레이딩 봇 자동 실행 스크립트
cd {PROJECT_DIR}
{VENV_PYTHON} {SCRIPT_PATH} >> {LOG_PATH} 2>&1
"""

with open(SHELL_SCRIPT_PATH, "w") as f:
    f.write(shell_content)
os.chmod(SHELL_SCRIPT_PATH, 0o755)

# 2. launchd plist 파일 생성 (평일 오후 4시 실행)
# Weekday: 1(Mon) ~ 5(Fri)
days = [1, 2, 3, 4, 5]
calendar_intervals = ""
for day in days:
    calendar_intervals += f"""
        <dict>
            <key>Weekday</key>
            <integer>{day}</integer>
            <key>Hour</key>
            <integer>16</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>"""

plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{SHELL_SCRIPT_PATH}</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>{calendar_intervals}
    </array>
    <key>StandardOutPath</key>
    <string>{LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>{LOG_PATH}</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""

with open(PLIST_PATH, "w") as f:
    f.write(plist_content)

print(f"Setup complete.")
print(f"Shell script: {SHELL_SCRIPT_PATH}")
print(f"Plist file: {PLIST_PATH}")
