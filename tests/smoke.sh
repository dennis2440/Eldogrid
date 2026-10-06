#!/usr/bin/env bash
# Quick check that every endpoint answers. Run with the server up:  bash tests/smoke.sh
B=${1:-http://localhost:8000}
for p in /health /dashboard/markers /dashboard/stats /dashboard/alerts /climate/risk /climate/alerts /waste/reports /sms/outbox; do
  printf "%-22s" "$p"; curl -s -o /dev/null -w "%{http_code}\n" "$B$p"
done
printf "%-22s" "POST /ussd"; curl -s -X POST "$B/ussd" -d "sessionId=1&serviceCode=*384#&phoneNumber=254700000001&text="; echo
printf "%-22s" "POST /alert/trigger"; curl -s -X POST "$B/climate/alert/trigger" -o /dev/null -w "%{http_code}\n"
