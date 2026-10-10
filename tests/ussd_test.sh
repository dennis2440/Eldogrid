#!/usr/bin/env bash
# Walks every USSD path and checks the reply. Run with the server up:
#   python -m app.db.seed && bash tests/ussd_test.sh
# TIP: set MOCK_MPESA_AUTO_CONFIRM_SECONDS=0 in .env first, so payments stay PENDING until we confirm them here.
B=${1:-http://localhost:8000}
PHONE="+254700000001"        # seeded farmer: maize, loam, wallet KES 500
NEW="+254799999999"          # unknown number
PASS=0; FAIL=0

ussd() {   # ussd <phone> <text> <expected substring> <label>
  local out
  out=$(curl -s -X POST "$B/ussd" --data-urlencode "sessionId=t1" --data-urlencode "serviceCode=*384#" \
        --data-urlencode "phoneNumber=$1" --data-urlencode "text=$2")
  if echo "$out" | grep -qF -- "$3"; then PASS=$((PASS+1)); printf "  ok   %-34s\n" "$4"
  else FAIL=$((FAIL+1)); printf "  FAIL %-34s expected [%s]\n       got: %s\n" "$4" "$3" "$out"; fi
}
post() { curl -s -X POST "$B$1" -H "Content-Type: application/json" -d "$2"; }

echo "Main menu & advice"
ussd $PHONE ""        "CON Welcome to EldoGrid"  "main menu"
ussd $PHONE "1"       "END "                      "advice (known farmer)"
ussd $NEW   "1"       "Select your crop"          "new farmer: crop prompt"
ussd $NEW   "1*1"     "Select your soil"          "new farmer: soil prompt"
ussd $NEW   "1*1*2"   "END "                      "new farmer: advice saved"
ussd $NEW   "1"       "END "                      "new farmer remembered"

echo "Order with wallet"
ussd $PHONE "2"       "Enter kg"                  "order: quantity prompt"
ussd $PHONE "2*50"    "Pay from wallet"           "order: payment menu"
ussd $PHONE "2*50*1"  "Order confirmed"           "order paid from wallet"
ussd $PHONE "4"       "KES 50"                    "balance after order"
ussd $PHONE "2*50*1"  "Wallet too low"            "wallet too low"

echo "Order with mock M-Pesa"
ussd $PHONE "2*30*2"  "M-Pesa prompt sent"        "order via M-Pesa"
R=$(post /mock/mpesa/callback '{"ResultCode":0}')
echo "$R" | grep -q '"status":"PAID"' && { PASS=$((PASS+1)); echo "  ok   callback marks order PAID"; } || { FAIL=$((FAIL+1)); echo "  FAIL callback: $R"; }
R=$(post /mock/mpesa/callback '{"ResultCode":0}')
echo "$R" | grep -q 'no pending' && { PASS=$((PASS+1)); echo "  ok   no double confirm"; } || { FAIL=$((FAIL+1)); echo "  FAIL double confirm: $R"; }

echo "Top up"
ussd $PHONE "3"       "top-up amount"             "topup: amount prompt"
ussd $PHONE "3*500"   "M-Pesa prompt sent"        "topup: prompt sent"
post /mock/mpesa/callback '{"ResultCode":0}' >/dev/null
ussd $PHONE "4"       "KES 550"                   "balance after top-up"

echo "PAY keyword by SMS"
ussd $PHONE "3*100"   "M-Pesa prompt sent"        "topup 100 pending"
curl -s -X POST "$B/sms/incoming" --data-urlencode "from=$PHONE" --data-urlencode "text=pay" >/dev/null
ussd $PHONE "4"       "KES 650"                   "PAY SMS confirmed top-up"

echo "Language"
ussd $PHONE "5"       "Choose language"           "language menu"
ussd $PHONE "5*2"     "Lugha imewekwa"            "switch to Swahili"
ussd $PHONE ""        "Karibu EldoGrid"           "menu in Swahili"
ussd $PHONE "5*1"     "Language set to English"   "back to English"

echo "Bad input (should never crash)"
ussd $PHONE "9"       "Invalid choice"            "unknown menu option"
ussd $PHONE "2*abc"   "whole number"              "quantity not a number"
ussd $PHONE "2*5"     "whole number"              "quantity too small"
ussd $PHONE "2*20*7"  "Invalid choice"            "bad payment option"
ussd $PHONE "3*5"     "whole number"              "top-up too small"
ussd $PHONE "1*1*1*1" "Invalid"                   "too many steps"

echo "SMS outbox"
N=$(curl -s "$B/sms/outbox" | grep -o '"message"' | wc -l)
[ "$N" -gt 0 ] && { PASS=$((PASS+1)); echo "  ok   outbox has $N messages"; } || { FAIL=$((FAIL+1)); echo "  FAIL outbox empty"; }

echo; echo "passed: $PASS   failed: $FAIL"; [ "$FAIL" -eq 0 ]
