# M4: Africa's Talking sandbox setup (step by step)

Why we need this: our app can't talk to phones by itself. Africa's Talking (AT) is the middleman: a farmer dials a code, AT receives it and forwards it to OUR server as an HTTP request (a "callback"), and shows our reply on the phone. In the sandbox this all happens on AT's web **simulator**, not on real phones.

## 1. Create the account
1. Go to africastalking.com and sign up (free).
2. Log in and click **Go to Sandbox App**. The sandbox username is `sandbox`.
3. Create an API key (Settings -> API Key) while you are in the sandbox. Treat it like a password.
4. Put them in your own `.env` (never commit it): 
   ```
   AT_USERNAME=sandbox
   AT_API_KEY=<your sandbox key>
   ```
Menu names can change, so if a button isn't where this says, look for the same words nearby.

## 2. Give AT a public URL (callback)
AT's servers can't reach `localhost`. Pick ONE:
- **Deployed URL** (best): M5 deploys the app, you use `https://<their-url>`.
- **Tunnel:** run `uvicorn app.main:app --port 8000`, then in a second terminal use a tunnel tool (ngrok or cloudflared) pointing at port 8000. Free tunnel URLs usually change on restart, so you must update the callback in AT every time.
Check it works first: open `<public-url>/health` in a browser. You must see `{"status":"ok"}`.

## 3. Create the USSD channel
1. In the sandbox dashboard open **USSD** -> **Create Channel**.
2. Pick the shared service code the dashboard offers (it looks like `*384*` plus a channel number you choose, for example `*384*1234#`). The channel number must be unique, so try another if taken.
3. Callback URL: `<public-url>/ussd`
4. Create it. Write down the full code. **That is your demo code, not plain `*384#`.**

## 4. Test it on the simulator
1. Open the AT simulator (link in the sandbox dashboard, or search "Africa's Talking simulator").
2. Enter a phone number such as `+254700000001` (seeded farmer with wallet money).
3. Choose USSD, dial your code. You should see "Welcome to EldoGrid".
4. If it fails: look at your server terminal. A request arriving there means AT reached you and the bug is in our code. Nothing arriving means the callback URL is wrong.

## 5. SMS (optional for the demo)
- Our code ALWAYS shows every SMS on the dashboard "phone screen" (the outbox), so SMS works for the pitch without any AT SMS setup.
- Real SMS delivery to the simulator: set `DEMO_MODE=false` in `.env`. In the dashboard, SMS -> Shortcodes lets you create a test shortcode, and its callback URL is `<public-url>/sms/incoming` (used for the `PAY` keyword).
- Sandbox messages show in the simulator, not on real phones. Sending to real phones needs a live AT account (top-up, sender ID approval, can take time), so decide early if you want that.

## 6. Quick checks before the team demo
- [ ] `bash tests/ussd_test.sh` passes locally (needs `MOCK_MPESA_AUTO_CONFIRM_SECONDS=0` in `.env`).
- [ ] Dial the real simulator code and walk: advice, order via wallet, order via M-Pesa, top-up.
- [ ] After a "pending" payment, confirm it with the dashboard button or `curl -X POST <url>/mock/mpesa/callback -H "Content-Type: application/json" -d '{}'`.
- [ ] Decide for the stage demo: auto-confirm (`MOCK_MPESA_AUTO_CONFIRM_SECONDS=5`, hands-free) or manual button (`0`, more control).
