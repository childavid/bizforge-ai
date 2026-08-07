# BizForge

BizForge is a simple client, invoice, and business-document workspace for small service businesses. It is intentionally focused: a business can keep client records, create invoices and proposals, track invoice status, export real PDFs, and download a CSV backup.

## Run locally

1. Create a private `.env` file from `.env.example`.
2. Install the packages in `requirements.txt`.
3. Start the app with `streamlit run business_ai.py`.

## Free local AI writing

The Email Writer, Social Media Posts, and Business Ideas tools can use [Ollama](https://ollama.com/), a free local AI runtime. This keeps prompts on the computer running BizForge and does not require an AI API key.

1. Install Ollama and run `ollama pull llama3.2` once.
2. Keep Ollama running, then start BizForge normally.
3. Optionally set `OLLAMA_MODEL` in `.env` to another model installed in Ollama.

If Ollama is not installed or is temporarily unavailable, BizForge still creates a tailored smart draft. Set `BIZFORGE_AI_PROVIDER=disabled` in `.env` to always use those built-in drafts.

For local use without payments, leave `BACKEND_URL` blank and keep `PAYMENTS_ENABLED=false`.

## Owner email notifications

BizForge emails `childavid558@gmail.com` when an account is created and when the existing Flutterwave webhook verifies a payment. It never sends a payment email for an unverified callback or a duplicate webhook retry.

To activate delivery, use `childavid558@gmail.com`'s Gmail [App Password](https://support.google.com/accounts/answer/185833) as `SMTP_PASSWORD` in the private `.env` file. Do not use the normal Gmail password. The recipient, Gmail SMTP host, port, sender address, and username are already configured in `.env`; restart the Streamlit and Flask services after adding the App Password.

## Public app-integration webhook

The Flask API now exposes a signed endpoint for online integrations:

```text
POST https://your-api-domain.example/app-webhook
```

Set a long random `APP_WEBHOOK_SECRET` in the private environment first. Send JSON with a unique `event_id`, an `event` name, and an object `data`. Calculate `X-BizForge-Signature` as the hexadecimal HMAC-SHA256 of the exact request body using `APP_WEBHOOK_SECRET`.

```json
{
  "event_id": "crm-lead-00042",
  "event": "lead.created",
  "data": {"name": "Ada", "source": "website"}
}
```

Accepted events are recorded once and send an owner notification. Repeated `event_id` values return `duplicate` without another notification. This endpoint deliberately cannot create accounts, upgrade plans, or mark payments as successful; the Flutterwave payment webhook remains the only payment-completion route.

To put the actual BizForge screens online, deploy the Streamlit app and the Flask API to public HTTPS hosts, then set `BACKEND_URL` to the Flask API address. A webhook is an integration endpoint; it does not host the web app by itself.

## Production setup

Run the Streamlit application and the Flask payment API on services with persistent storage. The Flask WSGI entry point is `backend.app:app`.
For a PythonAnywhere deployment and signed webhook test, follow [DEPLOYMENT.md](DEPLOYMENT.md).

Before accepting payments:

1. Create fresh Flutterwave API keys and a webhook secret hash. Any previous key may have been written to old application logs.
2. Put the values only in the server's private environment; never commit `.env`.
3. Set Flutterwave's webhook URL to `https://your-domain.example/flutterwave-webhook`.
4. Make a sandbox payment. Confirm the plan changes to Pro only after the webhook verifies the payment's transaction reference, amount, currency, and customer email.
5. Set `PAYMENTS_ENABLED=true` only after that test succeeds.
6. Configure a daily backup of the SQLite database or move to managed Postgres before storing important customer records at scale.

## Data responsibility

Each account sees only records saved under its signed-in email. Users can download their client and invoice register from Settings. The application does not yet provide password-reset email, multi-user teams, or automated cloud backup; do not promise those features to customers until they are added.
