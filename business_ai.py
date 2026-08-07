"""BizForge: client records, invoices, and practical business templates."""

import csv
import io
import os
from datetime import date, datetime

import requests
import streamlit as st
from dotenv import load_dotenv

from database.db import (
    FREE_DAILY_LIMIT,
    add_client,
    authenticate_user,
    can_use_feature,
    create_user,
    get_all_usage,
    get_business_ideas,
    get_business_name,
    get_clients,
    get_emails,
    get_history,
    get_invoices,
    get_plan,
    get_proposals,
    get_social_posts,
    increment_usage,
    init_db,
    save_business_idea,
    save_email,
    save_invoice,
    save_proposal,
    save_social_post,
    save_to_history,
    update_invoice_status,
)
from utils.currency import format_currency
from utils.export_utils import export_section
from utils.notifications import notify_new_signup


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
FEATURES = ["invoice", "proposal", "email", "social_media", "business_idea"]

st.set_page_config(page_title="BizForge", page_icon="📁", layout="wide")


@st.cache_resource(show_spinner=False)
def initialize_database():
    """Run schema checks once per app process, not on every user interaction."""
    init_db()


initialize_database()


def apply_futuristic_theme():
    """Apply presentation-only styling without changing app behaviour."""
    st.markdown(
        """
        <style>
            :root {
                --ink: #f7f8ff;
                --muted: #b9c0e5;
                --glass: rgba(14, 20, 52, 0.68);
                --line: rgba(166, 186, 255, 0.22);
                --cyan: #55e7ff;
                --violet: #a878ff;
                --pink: #ff73ce;
            }

            [data-testid="stAppViewContainer"] {
                background-color: #050816;
                background-image:
                    radial-gradient(circle at 12% 18%, rgba(63, 226, 255, 0.22), transparent 29%),
                    radial-gradient(circle at 86% 13%, rgba(190, 104, 255, 0.22), transparent 27%),
                    radial-gradient(circle at 74% 82%, rgba(255, 87, 190, 0.19), transparent 30%),
                    radial-gradient(circle at 22% 90%, rgba(91, 103, 255, 0.16), transparent 28%),
                    linear-gradient(130deg, #06091b 0%, #0b1030 48%, #100a2a 100%);
                background-size: 135% 135%;
                animation: aurora-drift 20s ease-in-out infinite alternate;
            }

            [data-testid="stAppViewContainer"]::before {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background-image:
                    linear-gradient(rgba(146, 164, 255, 0.035) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(146, 164, 255, 0.035) 1px, transparent 1px);
                background-size: 36px 36px;
                mask-image: linear-gradient(to bottom, rgba(0,0,0,0.65), transparent 90%);
            }

            @keyframes aurora-drift {
                from { background-position: 0% 12%; }
                to { background-position: 100% 88%; }
            }

            @keyframes glow-pulse {
                0%, 100% { box-shadow: 0 0 18px rgba(85, 231, 255, 0.18), 0 0 35px rgba(168, 120, 255, 0.10); }
                50% { box-shadow: 0 0 25px rgba(85, 231, 255, 0.32), 0 0 52px rgba(255, 115, 206, 0.18); }
            }

            html, body, [class*="css"], [data-testid="stAppViewContainer"] {
                color: var(--ink);
                font-family: "Segoe UI", "Inter", sans-serif;
            }

            [data-testid="stHeader"] {
                background: rgba(5, 8, 22, 0.30);
                backdrop-filter: blur(18px);
            }

            [data-testid="stSidebar"] > div:first-child {
                background:
                    radial-gradient(circle at 15% 4%, rgba(85, 231, 255, 0.20), transparent 30%),
                    radial-gradient(circle at 88% 32%, rgba(255, 115, 206, 0.16), transparent 35%),
                    linear-gradient(180deg, rgba(10, 16, 43, 0.96), rgba(5, 8, 24, 0.94));
                border-right: 1px solid var(--line);
            }

            h1, h2, h3 {
                color: var(--ink) !important;
                letter-spacing: -0.035em;
                text-shadow: 0 0 22px rgba(85, 231, 255, 0.20);
            }

            h1 {
                background: linear-gradient(100deg, #f8fbff 10%, var(--cyan) 43%, var(--pink) 78%, #f8fbff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            p, label, [data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] p {
                color: var(--muted);
            }

            [data-testid="stMetric"],
            [data-testid="stDataFrame"],
            [data-testid="stExpander"],
            [data-testid="stForm"] {
                background: var(--glass);
                border: 1px solid var(--line);
                border-radius: 18px;
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
            }

            [data-testid="stMetric"] {
                padding: 1.05rem;
                min-height: 116px;
                transition: transform 240ms ease, border-color 240ms ease, box-shadow 240ms ease;
                animation: glow-pulse 5s ease-in-out infinite;
            }

            [data-testid="stMetric"]:hover,
            [data-testid="stExpander"]:hover {
                transform: translateY(-5px);
                border-color: rgba(85, 231, 255, 0.56);
                box-shadow: 0 14px 38px rgba(0, 0, 0, 0.30), 0 0 26px rgba(168, 120, 255, 0.20);
            }

            [data-testid="stMetricLabel"] p,
            [data-testid="stMetricValue"] {
                color: var(--ink) !important;
            }

            [data-testid="stForm"] {
                padding: 1.15rem 1.25rem 0.55rem;
                animation: glow-pulse 7s ease-in-out infinite;
            }

            .stTextInput input, .stTextArea textarea, .stNumberInput input,
            [data-baseweb="select"] > div, [data-baseweb="input"] > div {
                color: var(--ink) !important;
                background: rgba(5, 10, 31, 0.60) !important;
                border-color: rgba(148, 172, 255, 0.30) !important;
                border-radius: 12px !important;
                transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
            }

            .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
                border-color: var(--cyan) !important;
                box-shadow: 0 0 0 1px rgba(85, 231, 255, 0.55), 0 0 20px rgba(85, 231, 255, 0.16) !important;
                transform: translateY(-1px);
            }

            .stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a,
            [data-testid="stFormSubmitButton"] > button {
                color: #ffffff !important;
                font-weight: 700;
                border: 1px solid rgba(159, 222, 255, 0.48) !important;
                border-radius: 12px !important;
                background: linear-gradient(105deg, #13355c, #3b236e 55%, #6b2458) !important;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.64);
                box-shadow: 0 5px 20px rgba(85, 231, 255, 0.16), 0 5px 28px rgba(255, 115, 206, 0.10);
                transition: transform 190ms ease, box-shadow 190ms ease, filter 190ms ease;
            }

            .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stLinkButton"] a:hover,
            [data-testid="stFormSubmitButton"] > button:hover {
                transform: translateY(-3px) scale(1.012);
                filter: brightness(1.20);
                box-shadow: 0 11px 30px rgba(85, 231, 255, 0.34), 0 11px 40px rgba(255, 115, 206, 0.24);
            }

            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                gap: 0.5rem;
                border-bottom: 1px solid var(--line);
            }

            [data-testid="stTabs"] button[role="tab"] {
                color: var(--muted);
                border-radius: 10px 10px 0 0;
            }

            [data-testid="stTabs"] button[aria-selected="true"] {
                color: var(--cyan) !important;
                background: rgba(85, 231, 255, 0.08);
                text-shadow: 0 0 14px rgba(85, 231, 255, 0.55);
            }

            [data-testid="stAlert"] {
                border-radius: 14px;
                backdrop-filter: blur(14px);
            }

            [data-testid="stDataFrame"] {
                overflow: hidden;
            }

            hr {
                border-color: rgba(148, 172, 255, 0.18) !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_futuristic_theme()


def init_state():
    defaults = {"logged_in": False, "email": "", "plan": "free", "pending_payment": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def load_plan(email):
    """Use the payment server's plan when available; local mode remains usable."""
    if not BACKEND_URL:
        return get_plan(email)
    try:
        response = requests.get(f"{BACKEND_URL}/plan/{email}", timeout=2)
        response.raise_for_status()
        plan = response.json().get("plan", "free")
        return plan if plan in {"free", "pro"} else "free"
    except (requests.RequestException, ValueError):
        return get_plan(email)


def sign_out():
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.plan = "free"
    st.session_state.pending_payment = None
    st.rerun()


def account_screen():
    st.title("BizForge")
    st.caption("Keep client records, quotes, invoices, and business documents together.")
    login_tab, create_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            if authenticate_user(email, password):
                st.session_state.logged_in = True
                st.session_state.email = email.strip().lower()
                st.session_state.plan = load_plan(st.session_state.email)
                st.rerun()
            st.error("Incorrect email or password.")

    with create_tab:
        with st.form("create_account_form"):
            business_name = st.text_input("Business name")
            email = st.text_input("Work email", key="create_email")
            password = st.text_input("Password (at least 8 characters)", type="password", key="create_password")
            confirmation = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create free account", use_container_width=True)
        if submitted:
            if password != confirmation:
                st.error("Passwords do not match.")
            else:
                try:
                    created = create_user(email, password, business_name)
                    if not created:
                        st.error("An account already uses this email. Please log in instead.")
                    else:
                        notify_new_signup(email.strip().lower(), business_name)
                        st.success("Account created. You can log in now.")
                except ValueError as exc:
                    st.error(str(exc))


def feature_allowed(feature):
    allowed, remaining = can_use_feature(st.session_state.email, feature, st.session_state.plan)
    if allowed:
        return True
    st.error(f"Today's free limit has been reached for this tool ({FREE_DAILY_LIMIT} uses).")
    st.info("Upgrade to Pro for unlimited use.")
    return False


def backup_csv(clients, invoices):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Record type", "Name / number", "Client", "Status", "Amount", "Currency", "Due date", "Created at"])
    for client in clients:
        writer.writerow(["Client", client["name"], "", "", "", "", "", client["created_at"]])
    for invoice in invoices:
        writer.writerow(
            [
                "Invoice",
                invoice["invoice_number"] or f"Legacy #{invoice['id']}",
                invoice["client"],
                invoice["status"],
                invoice["amount"],
                invoice["currency"],
                invoice["due_date"],
                invoice["created_at"],
            ]
        )
    return buffer.getvalue().encode("utf-8")


init_state()
if not st.session_state.logged_in:
    account_screen()
    st.stop()

email = st.session_state.email
business_name = get_business_name(email)

st.sidebar.title("BizForge")
st.sidebar.caption(business_name)
st.sidebar.write(email)
if st.session_state.plan == "pro":
    st.sidebar.success("Pro plan")
else:
    st.sidebar.info("Free plan")
    usage = get_all_usage(email)
    st.sidebar.caption("Today's template uses")
    for feature in FEATURES:
        st.sidebar.write(f"{feature.replace('_', ' ').title()}: {usage.get(feature, 0)}/{FREE_DAILY_LIMIT}")
if st.sidebar.button("Log out", use_container_width=True):
    sign_out()

tool = st.sidebar.selectbox(
    "Workspace",
    [
        "Dashboard",
        "Clients",
        "Invoice Generator",
        "Invoice Register",
        "Proposal Generator",
        "Email Writer",
        "Social Media Posts",
        "Business Ideas",
        "History",
        "Settings",
    ],
)

# Avoid loading every saved record on pages that do not use them. This matters
# when a business has built up a large history of invoices and clients.
clients = get_clients(email) if tool in {"Dashboard", "Clients", "Invoice Generator", "Settings"} else []
invoices = get_invoices(email) if tool in {"Dashboard", "Invoice Register", "Settings"} else []


if tool == "Dashboard":
    st.title(f"{business_name} workspace")
    st.caption("Your client records and business documents in one place.")
    paid_total = sum(float(item["amount"]) for item in invoices if item["status"] == "paid")
    open_total = sum(float(item["amount"]) for item in invoices if item["status"] in {"sent", "overdue"})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clients", len(clients))
    col2.metric("Invoices", len(invoices))
    col3.metric("Outstanding", format_currency(open_total))
    col4.metric("Recorded paid", format_currency(paid_total))
    st.divider()
    st.subheader("Recent invoices")
    if invoices:
        st.dataframe(
            [
                {
                    "Invoice": item["invoice_number"] or f"Legacy #{item['id']}",
                    "Client": item["client"],
                    "Amount": format_currency(item["amount"], item["currency"]),
                    "Status": item["status"].title(),
                    "Due date": item["due_date"] or "—",
                }
                for item in invoices[:8]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Add a client and create your first invoice to begin.")


elif tool == "Clients":
    st.title("Clients")
    st.caption("Add a client once, then select them when creating invoices and proposals.")
    with st.form("client_form", clear_on_submit=True):
        name = st.text_input("Client or company name")
        contact_email = st.text_input("Contact email (optional)")
        phone = st.text_input("Phone (optional)")
        address = st.text_area("Address (optional)", height=70)
        notes = st.text_area("Notes (optional)", height=100)
        submitted = st.form_submit_button("Save client")
    if submitted:
        try:
            add_client(email, name, contact_email, phone, address, notes)
            st.success("Client saved.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    if clients:
        st.subheader("Saved clients")
        st.dataframe(
            [
                {
                    "Client": item["name"],
                    "Email": item["contact_email"] or "—",
                    "Phone": item["phone"] or "—",
                    "Notes": item["notes"] or "—",
                }
                for item in clients
            ],
            use_container_width=True,
            hide_index=True,
        )


elif tool == "Invoice Generator":
    st.title("Invoice Generator")
    if feature_allowed("invoice"):
        saved_names = [item["name"] for item in clients]
        with st.form("invoice_form"):
            selected_client = st.selectbox("Saved client", ["Add a new client…", *saved_names])
            client = st.text_input("Client name", value="" if selected_client == "Add a new client…" else selected_client)
            service = st.text_input("Service or product")
            description = st.text_area("Description")
            col1, col2, col3 = st.columns(3)
            quantity = col1.number_input("Quantity", min_value=1.0, value=1.0, step=1.0)
            rate = col2.number_input("Rate", min_value=0.0, value=0.0, step=100.0)
            tax = col3.number_input("Tax (%)", min_value=0.0, max_value=100.0, value=0.0)
            due_date = st.date_input("Due date", value=date.today())
            currency = st.selectbox("Currency", ["NGN", "USD"])
            submitted = st.form_submit_button("Create invoice", use_container_width=True)
        if submitted:
            subtotal = float(quantity) * float(rate)
            tax_amount = subtotal * (float(tax) / 100)
            total = subtotal + tax_amount
            content = (
                f"{business_name}\n\n"
                f"Client: {client}\nService: {service}\nDescription: {description}\n\n"
                f"Subtotal: {format_currency(subtotal, currency)}\n"
                f"Tax: {format_currency(tax_amount, currency)}\n"
                f"Total: {format_currency(total, currency)}\n"
                f"Due date: {due_date.isoformat()}"
            )
            try:
                if selected_client == "Add a new client…":
                    add_client(email, client)
                invoice_number = save_invoice(
                    email,
                    client,
                    service,
                    content,
                    total,
                    due_date=due_date,
                    currency=currency,
                    status="draft",
                )
                increment_usage(email, "invoice")
                save_to_history(email, "invoice", content)
                st.success(f"Invoice {invoice_number} created as a draft.")
                st.text_area("Invoice", content, height=260)
                export_section(content, "Invoice", invoice_number)
            except ValueError as exc:
                st.error(str(exc))


elif tool == "Invoice Register":
    st.title("Invoice Register")
    st.caption("Keep invoice status up to date so you can see what is still owed.")
    if not invoices:
        st.info("No invoices yet.")
    else:
        options = {
            f"{item['invoice_number'] or f'Legacy #{item["id"]}'} — {item['client']} — {format_currency(item['amount'], item['currency'])}": item
            for item in invoices
        }
        selected_label = st.selectbox("Invoice", list(options))
        selected = options[selected_label]
        current_status = selected["status"] if selected["status"] in {"draft", "sent", "paid", "overdue", "cancelled"} else "draft"
        new_status = st.selectbox(
            "Status",
            ["draft", "sent", "paid", "overdue", "cancelled"],
            index=["draft", "sent", "paid", "overdue", "cancelled"].index(current_status),
        )
        if st.button("Save status"):
            update_invoice_status(email, selected["id"], new_status)
            st.success("Invoice status updated.")
            st.rerun()
        st.divider()
        st.text_area("Invoice content", selected["content"], height=260)
        export_section(selected["content"], "Invoice", selected["invoice_number"] or f"invoice_{selected['id']}")


elif tool == "Proposal Generator":
    st.title("Proposal Generator")
    if feature_allowed("proposal"):
        with st.form("proposal_form"):
            client = st.text_input("Client")
            project = st.text_input("Project")
            scope = st.text_area("Scope of work")
            timeline = st.text_input("Timeline")
            budget = st.number_input("Budget", min_value=0.0, value=0.0, step=100.0)
            submitted = st.form_submit_button("Create proposal", use_container_width=True)
        if submitted:
            content = (
                f"{business_name}\n\nClient: {client}\nProject: {project}\n\n"
                f"Scope:\n{scope}\n\nTimeline: {timeline}\nBudget: {format_currency(budget)}"
            )
            try:
                save_proposal(email, client, project, content)
                increment_usage(email, "proposal")
                save_to_history(email, "proposal", content)
                st.success("Proposal created.")
                st.text_area("Proposal", content, height=260)
                export_section(content, "Proposal", f"proposal_{project}")
            except ValueError as exc:
                st.error(str(exc))


elif tool == "Email Writer":
    st.title("Email Template Writer")
    st.caption("Create an editable business email with free local AI. Review it before sending.")
    if feature_allowed("email"):
        with st.form("email_form"):
            recipient = st.text_input("Recipient name")
            purpose = st.text_area("Purpose or key message")
            tone = st.selectbox("Tone", ["Professional", "Warm", "Direct"])
            submitted = st.form_submit_button("Create email", use_container_width=True)
        if submitted:
            from utils.ai_assist import generate_email_assist

            template = generate_email_assist(purpose, recipient, tone)
            subject = template["subject"]
            body = template["body"]
            content = f"Subject: {subject}\n\n{body}"
            try:
                save_email(email, recipient, subject, content)
                increment_usage(email, "email")
                save_to_history(email, "email", content)
                st.success("Email template saved.")
                if template["used_ai"]:
                    st.caption("Generated with free local AI (Ollama).")
                else:
                    st.caption("Local AI was unavailable, so BizForge created an editable smart draft.")
                st.text_area("Email", content, height=280)
                export_section(content, "Email", f"email_{recipient}")
            except ValueError as exc:
                st.error(str(exc))


elif tool == "Social Media Posts":
    st.title("Social Media Template Writer")
    st.caption("Create a platform-aware draft with free local AI, then tailor it before posting.")
    if feature_allowed("social_media"):
        with st.form("social_form"):
            topic = st.text_area("Post topic or offer")
            col1, col2 = st.columns(2)
            platform = col1.selectbox("Platform", ["Instagram", "LinkedIn", "Facebook", "X / Twitter", "TikTok"])
            tone = col2.selectbox("Tone", ["Friendly", "Professional", "Bold", "Helpful"])
            goal = st.selectbox("Main goal", ["Build awareness", "Get enquiries", "Drive sales", "Grow engagement"])
            submitted = st.form_submit_button("Create post", use_container_width=True)
        if submitted:
            from utils.ai_assist import generate_social_post_assist

            template = generate_social_post_assist(topic, platform, tone, goal, business_name)
            content = template["post"]
            try:
                save_social_post(email, template["platform"], content)
                increment_usage(email, "social_media")
                save_to_history(email, "social_post", content)
                st.success("Social post template saved.")
                if template["used_ai"]:
                    st.caption("Generated with free local AI (Ollama).")
                else:
                    st.caption("Local AI was unavailable, so BizForge created an editable smart draft.")
                st.text_area("Post", content, height=250)
                export_section(content, "Social post", f"social_{template['platform']}")
            except ValueError as exc:
                st.error(str(exc))


elif tool == "Business Ideas":
    st.title("Business Idea Templates")
    st.caption("Turn an interest into a practical concept with free local AI and a lean launch plan.")
    if feature_allowed("business_idea"):
        with st.form("idea_form"):
            interest = st.text_area("Industry or interest")
            audience = st.text_input("Target customer (optional)")
            starting_budget = st.text_input("Starting budget or resources (optional)")
            submitted = st.form_submit_button("Create idea", use_container_width=True)
        if submitted:
            from utils.ai_assist import generate_business_idea_assist

            template = generate_business_idea_assist(interest, audience, starting_budget)
            content = template["idea"]
            try:
                save_business_idea(email, template["category"], content)
                increment_usage(email, "business_idea")
                save_to_history(email, "idea", content)
                st.success("Business idea template saved.")
                if template["used_ai"]:
                    st.caption("Generated with free local AI (Ollama).")
                else:
                    st.caption("Local AI was unavailable, so BizForge created an editable smart draft.")
                st.text_area("Business idea", content, height=280)
                export_section(content, "Business idea", f"idea_{template['category']}")
            except ValueError as exc:
                st.error(str(exc))


elif tool == "History":
    st.title("Document History")
    labels = {"All": None, "Invoice": "invoice", "Proposal": "proposal", "Email": "email", "Social post": "social_post", "Business idea": "idea"}
    selected_label = st.selectbox("Filter", list(labels))
    items = get_history(email, labels[selected_label])
    st.caption(f"{len(items)} saved document(s)")
    if not items:
        st.info("Nothing is saved here yet.")
    for item in items:
        try:
            saved_at = datetime.fromisoformat(item["created_at"]).strftime("%d %b %Y, %H:%M")
        except (TypeError, ValueError):
            saved_at = item["created_at"]
        with st.expander(f"{item['feature_type'].replace('_', ' ').title()} — {saved_at}"):
            st.text_area("Content", item["content"], height=180, key=f"history_{item['id']}")
            export_section(item["content"], item["feature_type"].title(), f"history_{item['id']}")


elif tool == "Settings":
    st.title("Settings")
    st.subheader("Account")
    st.write(f"Business: {business_name}")
    st.write(f"Email: {email}")
    st.write(f"Plan: {st.session_state.plan.title()}")
    st.divider()
    st.subheader("Your data backup")
    st.caption("Download your client and invoice register regularly. Keep the file somewhere private.")
    st.download_button(
        "Download clients and invoices CSV",
        data=backup_csv(clients, invoices),
        file_name=f"bizforge_backup_{date.today().isoformat()}.csv",
        mime="text/csv",
    )
    st.divider()
    st.subheader("Upgrade to Pro")
    if st.session_state.plan == "pro":
        st.success("Your account has Pro access.")
    elif not BACKEND_URL:
        st.info("Secure checkout is not configured for this deployment yet.")
    else:
        st.caption("The secure checkout sets and verifies the current price before access is upgraded.")
        if st.button("Create secure checkout link", use_container_width=True):
            try:
                response = requests.post(f"{BACKEND_URL}/pay", json={"email": email}, timeout=12)
                payload = response.json()
                if response.ok and payload.get("status") == "success" and payload.get("link"):
                    st.session_state.pending_payment = payload.get("tx_ref")
                    st.success("Your secure checkout link is ready.")
                    st.markdown(f"[Open secure checkout]({payload['link']})")
                else:
                    st.error(payload.get("message", "Checkout is not available right now."))
            except (requests.RequestException, ValueError):
                st.error("Checkout is not available right now. Please try again later.")
        if st.button("Refresh plan status"):
            st.session_state.plan = load_plan(email)
            st.rerun()
