# Put BizForge online

This guide publishes the Flask API (payments and webhooks) on PythonAnywhere and explains how an online service can call the BizForge app webhook. A webhook is an API endpoint; the Streamlit user interface must be deployed separately before people can use the screens online.

## 1. Configure the private settings

Create a random webhook secret locally in PowerShell. Keep the result private.

```powershell
[Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()
```

Open the private `.env` file and set the result as the value of `APP_WEBHOOK_SECRET`:

```dotenv
APP_WEBHOOK_SECRET=paste-the-random-value-here
```

Also add the Gmail App Password as `SMTP_PASSWORD` if you want signup, payment, and integration-event notifications delivered to `childavid558@gmail.com`.

## 2. Deploy the Flask API on PythonAnywhere

These steps deploy the endpoint that receives `/flutterwave-webhook` and `/app-webhook`.

1. Upload or clone this project into `/home/<your-PythonAnywhere-username>/BusinessAI`.
2. In a PythonAnywhere Bash console, install the packages in a virtual environment:

   ```bash
   cd ~/BusinessAI
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. In the PythonAnywhere **Web** tab, create a new **Manual configuration** web app using **Flask** and the same Python version.
4. Set its virtualenv path to:

   ```text
   /home/<your-PythonAnywhere-username>/BusinessAI/.venv
   ```

5. Replace the generated WSGI-file contents with the following, changing the username once:

   ```python
   import os
   import sys

   project_root = "/home/<your-PythonAnywhere-username>/BusinessAI"
   if project_root not in sys.path:
       sys.path.insert(0, project_root)

   os.environ.setdefault("BIZFORGE_DB_PATH", f"{project_root}/saas.db")

   from backend.app import app as application
   ```

6. Copy your private `.env` file to the project folder. Set `BACKEND_URL` to your public API URL, for example:

   ```dotenv
   BACKEND_URL=https://<your-PythonAnywhere-username>.pythonanywhere.com
   ```

7. Click **Reload** in the Web tab, then visit:

   ```text
   https://<your-PythonAnywhere-username>.pythonanywhere.com/health
   ```

   A successful response is JSON with `"status": "ok"`.

8. In Flutterwave, set the payment webhook URL to:

   ```text
   https://<your-PythonAnywhere-username>.pythonanywhere.com/flutterwave-webhook
   ```

Do not enable `PAYMENTS_ENABLED=true` until a Flutterwave sandbox payment has verified successfully.

## 3. Let online services call the app webhook

The secure endpoint is:

```text
POST https://<your-PythonAnywhere-username>.pythonanywhere.com/app-webhook
```

The request body must contain a globally unique `event_id`, event name, and an object called `data`:

```json
{"event_id":"lead-2026-0001","event":"lead.created","data":{"name":"Ada","source":"website"}}
```

Sign the **exact** JSON body using HMAC-SHA256 and your `APP_WEBHOOK_SECRET`. Send the hexadecimal signature in the `X-BizForge-Signature` header, with an optional `sha256=` prefix.

This PowerShell example sends a test event. Replace the URL and secret placeholders locally; do not put the secret into a website, screenshot, or chat.

```powershell
$body = '{"event_id":"test-001","event":"integration.test","data":{"source":"PowerShell"}}'
$secret = '<your APP_WEBHOOK_SECRET>'
$hmac = [System.Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($secret))
$signature = [Convert]::ToHexString($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($body))).ToLower()

Invoke-RestMethod -Method Post `
  -Uri 'https://<your-PythonAnywhere-username>.pythonanywhere.com/app-webhook' `
  -ContentType 'application/json' `
  -Headers @{ 'X-BizForge-Signature' = "sha256=$signature" } `
  -Body $body
```

The first accepted event returns `202` with `"status":"accepted"`; sending the same `event_id` again returns `200` with `"status":"duplicate"` and does not create another email notification.

## Deploy the Streamlit user interface

The Flask deployment above provides the API and webhook URLs only. To let customers use the BizForge screens online, deploy `business_ai.py` on a Streamlit-capable host and set its `BACKEND_URL` environment variable to the Flask API URL.

Because BizForge stores customer records in SQLite, use persistent storage for any public deployment or migrate to managed Postgres before relying on a free host with an ephemeral filesystem. Keep the Streamlit app and Flask API on HTTPS, and never commit `.env` or `saas.db`.
