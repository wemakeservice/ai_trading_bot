#!/bin/bash
# AI 트레이딩 봇 자동 실행 스크립트
cd /Users/naewon/workspace/ai_trading_bot
/Users/naewon/workspace/ai_trading_bot/venv/bin/python3 /Users/naewon/workspace/ai_trading_bot/daily_scanner.py >> /Users/naewon/workspace/ai_trading_bot/automation.log 2>&1
