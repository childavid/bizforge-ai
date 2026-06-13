import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

from database.db import (
    init_db,
    create_user,
    get_plan,
    save_invoice,
    save_proposal,
    get_invoices,
    get_proposals,
    can_use_feature,
    increment_usage,
    get_all_usage,
    FREE_DAILY_LIMIT,
    save_email,
    get_emails,
    save_social_post,
    get_social_posts,
    save_business_idea,
    get_business_ideas,
    save_to_history,
    get_history
)

from datetime import datetime

BACKEND_URL = "https://chil.pythonanywhere.com"

# ================= INIT =================
st.set_page_config(page_title="BizForge AI", layout="wide")
init_db()


# ================= SESSION =================
def init_state():
    defaults = {
        "logged_in": False,
        "email": "",
        "plan": "free",
        "invoice_count": 0,
        "proposal_count": 0
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ================= LOGIN =================
def login():
    st.title("🔐 BizForge AI")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if email and password:

            st.session_state.logged_in = True
            st.session_state.email = email

            # STEP 5: create user in DB
            create_user(email)

            # STEP 5: load plan from backend API
            try:
                response = requests.get(f"{BACKEND_URL}/plan/{email}", timeout=10)
                response.raise_for_status()
                st.session_state.plan = response.json()["plan"]
            except requests.exceptions.Timeout:
                st.error("Backend request timed out. Defaulting to free plan.")
                st.session_state.plan = "free"
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to backend. Defaulting to free plan.")
                st.session_state.plan = "free"
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to fetch plan from backend: {e}. Defaulting to free plan.")
                st.session_state.plan = "free"
            except Exception as e:
                st.error(f"Unexpected error: {e}. Defaulting to free plan.")
                st.session_state.plan = "free"

            st.success("✅ Login successful — welcome to BizForge AI")
            st.rerun()

        else:
            st.error("Enter credentials")


if not st.session_state.logged_in:
    login()
    st.stop()

email = st.session_state.email


# ================= SIDEBAR =================
st.sidebar.title("BizForge AI")

st.sidebar.write(f"User: {email}")

# Show PRO badge
if st.session_state.plan == "pro":
    st.sidebar.success("🎉 PRO Plan")
else:
    st.sidebar.info(f"FREE Plan")

# Show usage for free users
if st.session_state.plan == "free":
    usage_data = get_all_usage(email)
    st.sidebar.divider()
    st.sidebar.write("📊 Daily Usage:")
    for feature, count in usage_data.items():
        remaining = FREE_DAILY_LIMIT - count
        st.sidebar.write(f"{feature}: {count}/{FREE_DAILY_LIMIT} ({remaining} left)")

tool = st.sidebar.selectbox(
    "Tool",
    [
        "Dashboard",
        "Invoice Generator",
        "Proposal Generator",
        "Email Writer",
        "Social Media Posts",
        "Business Ideas",
        "History",
        "Settings"
    ]
)


# ================= DASHBOARD =================
if tool == "Dashboard":
    # Hero Section
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1e88e5; margin-bottom: 0.5rem;'>BizForge AI</h1>
        <p style='color: #666; font-size: 1.2rem;'>Your AI-powered business automation suite</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Welcome Message
    st.markdown(f"### 👋 Welcome back, {email}")
    
    # Plan Status Section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.plan == "pro":
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; border-radius: 10px; color: white; text-align: center;'>
                <h3 style='margin: 0;'>🎉 PRO PLAN</h3>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem;'>Unlimited Access</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 1rem; border-radius: 10px; color: white; text-align: center;'>
                <h3 style='margin: 0;'>🆓 FREE PLAN</h3>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        usage_data = get_all_usage(email)
        total_usage = sum(usage_data.values())
        if st.session_state.plan == "free":
            remaining = (FREE_DAILY_LIMIT * len(usage_data)) - total_usage if usage_data else FREE_DAILY_LIMIT
            st.metric("Daily Usage", f"{total_usage} used", f"{remaining} remaining")
        else:
            st.metric("Daily Usage", "Unlimited")
    
    with col3:
        st.metric("Total Tools", "5")
    
    # Upgrade Button for FREE users
    if st.session_state.plan == "free":
        st.divider()
        col_upgrade = st.columns(1)[0]
        with col_upgrade:
            if st.button("🚀 Upgrade to PRO", key="dashboard_upgrade", use_container_width=True):
                st.info("👉 Go to Settings to upgrade your plan")
        st.divider()
    
    st.divider()
    
    # Tool Cards
    st.markdown("### 🛠️ Available Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 10px; 
                    background: #f8f9fa; margin-bottom: 1rem;'>
            <h4 style='color: #1e88e5; margin-top: 0;'>🧾 Invoice Generator</h4>
            <p style='color: #666; font-size: 0.9rem; margin-bottom: 1rem;'>Create professional invoices with automatic calculations</p>
        </div>
        """, unsafe_allow_html=True)
        can_use_inv, _ = can_use_feature(email, "invoice", st.session_state.plan)
        if can_use_inv or st.session_state.plan == "pro":
            st.success("✅ Available")
        else:
            st.error("❌ Limit reached")
    
    with col2:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 10px; 
                    background: #f8f9fa; margin-bottom: 1rem;'>
            <h4 style='color: #1e88e5; margin-top: 0;'>✍️ Proposal Generator</h4>
            <p style='color: #666; font-size: 0.9rem; margin-bottom: 1rem;'>Generate client proposals with structured content</p>
        </div>
        """, unsafe_allow_html=True)
        can_use_prop, _ = can_use_feature(email, "proposal", st.session_state.plan)
        if can_use_prop or st.session_state.plan == "pro":
            st.success("✅ Available")
        else:
            st.error("❌ Limit reached")
    
    with col3:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 10px; 
                    background: #f8f9fa; margin-bottom: 1rem;'>
            <h4 style='color: #1e88e5; margin-top: 0;'>📧 Email Writer</h4>
            <p style='color: #666; font-size: 0.9rem; margin-bottom: 1rem;'>Write professional business emails instantly</p>
        </div>
        """, unsafe_allow_html=True)
        can_use_email, _ = can_use_feature(email, "email", st.session_state.plan)
        if can_use_email or st.session_state.plan == "pro":
            st.success("✅ Available")
        else:
            st.error("❌ Limit reached")
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 10px; 
                    background: #f8f9fa; margin-bottom: 1rem;'>
            <h4 style='color: #1e88e5; margin-top: 0;'>📱 Social Media Posts</h4>
            <p style='color: #666; font-size: 0.9rem; margin-bottom: 1rem;'>Create engaging social media posts</p>
        </div>
        """, unsafe_allow_html=True)
        can_use_social, _ = can_use_feature(email, "social_media", st.session_state.plan)
        if can_use_social or st.session_state.plan == "pro":
            st.success("✅ Available")
        else:
            st.error("❌ Limit reached")
    
    with col5:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 10px; 
                    background: #f8f9fa; margin-bottom: 1rem;'>
            <h4 style='color: #1e88e5; margin-top: 0;'>💡 Business Ideas</h4>
            <p style='color: #666; font-size: 0.9rem; margin-bottom: 1rem;'>Get innovative business ideas based on your interests</p>
        </div>
        """, unsafe_allow_html=True)
        can_use_idea, _ = can_use_feature(email, "business_idea", st.session_state.plan)
        if can_use_idea or st.session_state.plan == "pro":
            st.success("✅ Available")
        else:
            st.error("❌ Limit reached")
    
    st.divider()
    
    # Quick Stats
    st.markdown("### 📈 Quick Stats")
    invoices = get_invoices(email)
    proposals = get_proposals(email)
    emails = get_emails(email)
    social_posts = get_social_posts(email)
    business_ideas = get_business_ideas(email)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Invoices", len(invoices))
    with col2:
        st.metric("Proposals", len(proposals))
    with col3:
        st.metric("Emails", len(emails))
    with col4:
        st.metric("Social Posts", len(social_posts))
    with col5:
        st.metric("Business Ideas", len(business_ideas))


# ================= INVOICE =================
elif tool == "Invoice Generator":
    st.title("🧾 Invoice Generator")

    # Check usage limit before allowing access
    can_use, remaining = can_use_feature(email, "invoice", st.session_state.plan)

    if not can_use:
        st.error(f"❌ Daily limit reached! You've used your {FREE_DAILY_LIMIT} free invoice generations for today.")
        st.info("🚀 Upgrade to PRO for unlimited access")
        st.info("👉 Go to Settings to upgrade your plan")
        st.stop()

    client = st.text_input("Client")
    service = st.text_input("Service")
    description = st.text_area("Description")

    qty = st.number_input("Quantity", value=1, min_value=0)
    rate = st.number_input("Rate", value=0.0, min_value=0.0)
    tax = st.slider("Tax %", 0, 25, 0)

    if st.button("Generate Invoice"):
        if not client or not service:
            st.error("Client and Service are required")
            st.stop()

        subtotal = float(qty) * float(rate)
        tax_amount = subtotal * (tax / 100)
        total = subtotal + tax_amount

        content = f"""
Client: {client}
Service: {service}
Description: {description}

Subtotal: {subtotal}
Tax: {tax_amount}
Total: {total}
"""

        save_invoice(email, client, service, content, total)
        increment_usage(email, "invoice")
        st.session_state.invoice_count += 1
        
        # Save to history
        save_to_history(email, "invoice", content)

        st.success("Invoice Created")
        st.write(content)
        
        # Export options
        from utils.export_utils import export_section
        export_section(content, "Invoice", f"invoice_{client}")


# ================= PROPOSAL =================
elif tool == "Proposal Generator":
    st.title("✍️ Proposal Generator")

    # Check usage limit before allowing access
    can_use, remaining = can_use_feature(email, "proposal", st.session_state.plan)

    if not can_use:
        st.error(f"❌ Daily limit reached! You've used your {FREE_DAILY_LIMIT} free proposal generations for today.")
        st.info("🚀 Upgrade to PRO for unlimited access")
        st.info("👉 Go to Settings to upgrade your plan")
        st.stop()

    client = st.text_input("Client")
    project = st.text_input("Project")
    scope = st.text_area("Scope")
    timeline = st.text_input("Timeline")
    budget = st.number_input("Budget", value=0.0, min_value=0.0)

    if st.button("Generate Proposal"):
        if not client or not project:
            st.error("Client and Project are required")
            st.stop()

        content = f"""
Client: {client}
Project: {project}

Scope:
{scope}

Timeline: {timeline}
Budget: {budget}
"""

        save_proposal(email, client, project, content)
        increment_usage(email, "proposal")
        st.session_state.proposal_count += 1
        
        # Save to history
        save_to_history(email, "proposal", content)

        st.success("Proposal Created")
        st.write(content)
        
        # Export options
        from utils.export_utils import export_section
        export_section(content, "Proposal", f"proposal_{project}")


# ================= EMAIL WRITER =================
elif tool == "Email Writer":
    st.title("📧 Email Writer")

    # Check usage limit before allowing access
    can_use, remaining = can_use_feature(email, "email", st.session_state.plan)

    if not can_use:
        st.error(f"❌ Daily limit reached! You've used your {FREE_DAILY_LIMIT} free email generations for today.")
        st.info("🚀 Upgrade to PRO for unlimited access")
        st.info("👉 Go to Settings to upgrade your plan")
        st.stop()

    recipient = st.text_input("Recipient Name")
    purpose = st.text_area("Email Purpose/Topic", help="Describe the purpose of this email (e.g., follow up, proposal, meeting request)")

    if st.button("Generate Email"):
        if not recipient or not purpose:
            st.error("Recipient and Purpose are required")
            st.stop()

        from utils.ai_assist import generate_email_assist
        email_data = generate_email_assist(purpose)

        subject = email_data["subject"]
        body = email_data["body"]

        # Replace placeholders
        body = body.replace("[Name]", recipient)

        content = f"""
Subject: {subject}

{body}
"""

        save_email(email, recipient, subject, content)
        increment_usage(email, "email")
        
        # Save to history
        save_to_history(email, "email", content)

        st.success("Email Generated")
        st.text_area("Email Content", content, height=300)
        
        # Export options
        from utils.export_utils import export_section
        export_section(content, "Email", f"email_{recipient}")


# ================= SOCIAL MEDIA GENERATOR =================
elif tool == "Social Media Posts":
    st.title("📱 Social Media Posts")

    # Check usage limit before allowing access
    can_use, remaining = can_use_feature(email, "social_media", st.session_state.plan)

    if not can_use:
        st.error(f"❌ Daily limit reached! You've used your {FREE_DAILY_LIMIT} free social media post generations for today.")
        st.info("🚀 Upgrade to PRO for unlimited access")
        st.info("👉 Go to Settings to upgrade your plan")
        st.stop()

    topic = st.text_area("Post Topic/Theme", help="Describe what you want to post about (e.g., product launch, tip, promotion)")

    if st.button("Generate Social Media Post"):
        if not topic:
            st.error("Topic is required")
            st.stop()

        from utils.ai_assist import generate_social_post_assist
        post_data = generate_social_post_assist(topic)

        platform = post_data["platform"]
        content = post_data["post"]

        save_social_post(email, platform, content)
        increment_usage(email, "social_media")
        
        # Save to history
        save_to_history(email, "social_post", content)

        st.success("Social Media Post Generated")
        st.info(f"Platform: {platform}")
        st.text_area("Post Content", content, height=250)
        
        # Export options
        from utils.export_utils import export_section
        export_section(content, "Social Media Post", f"social_post_{platform}")


# ================= BUSINESS IDEA GENERATOR =================
elif tool == "Business Ideas":
    st.title("💡 Business Ideas")

    # Check usage limit before allowing access
    can_use, remaining = can_use_feature(email, "business_idea", st.session_state.plan)

    if not can_use:
        st.error(f"❌ Daily limit reached! You've used your {FREE_DAILY_LIMIT} free business idea generations for today.")
        st.info("🚀 Upgrade to PRO for unlimited access")
        st.info("👉 Go to Settings to upgrade your plan")
        st.stop()

    interest = st.text_area("Industry/Interest", help="What industry or area are you interested in? (e.g., tech, ecommerce, education)")

    if st.button("Generate Business Idea"):
        if not interest:
            st.error("Industry/Interest is required")
            st.stop()

        from utils.ai_assist import generate_business_idea_assist
        idea_data = generate_business_idea_assist(interest)

        category = idea_data["category"]
        idea = idea_data["idea"]

        save_business_idea(email, category, idea)
        increment_usage(email, "business_idea")
        
        # Save to history
        save_to_history(email, "idea", idea)

        st.success("Business Idea Generated")
        st.info(f"Category: {category}")
        st.text_area("Business Idea", idea, height=300)
        
        # Export options
        from utils.export_utils import export_section
        export_section(idea, "Business Idea", f"business_idea_{category}")


# ================= HISTORY =================
elif tool == "History":
    st.title("📜 History")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        feature_filter = st.selectbox(
            "Filter by Type",
            ["All", "Invoice", "Proposal", "Email", "Social Post", "Business Idea"]
        )
    
    with col2:
        st.write(f"Total items: {len(get_history(email))}")
    
    st.divider()
    
    # Get history based on filter
    if feature_filter == "All":
        history_items = get_history(email)
    else:
        feature_map = {
            "Invoice": "invoice",
            "Proposal": "proposal",
            "Email": "email",
            "Social Post": "social_post",
            "Business Idea": "idea"
        }
        history_items = get_history(email, feature_map[feature_filter])
    
    if history_items:
        for item in history_items:
            item_id, item_email, feature_type, content, created_at = item
            
            # Format date
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(created_at)
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_date = created_at
            
            # Display item
            with st.expander(f"{feature_type.upper()} - {formatted_date}"):
                st.text_area("Content", content, height=150, key=f"history_{item_id}")
                
                # Export options for this item
                from utils.export_utils import export_section
                export_section(content, f"{feature_type.upper()}", f"history_{feature_type}_{item_id}")
    else:
        st.info("No history items found")


# ================= SETTINGS =================
elif tool == "Settings":
    st.title("⚙️ Settings")

    # ================= ACCOUNT INFO =================
    st.subheader("👤 Account Info")
    st.write("Email:", email)
    st.write("Plan:", st.session_state.plan.upper())

    st.divider()

    # ================= SIMPLE FLUTTERWAVE PAYMENT =================
    st.subheader("💳 Upgrade to PRO")

    import requests
    import uuid

    # ================= BUTTON =================

    if st.session_state.plan == "free":

        st.info("You are on FREE plan")

        if st.button("🚀 Upgrade to PRO"):

            # FIXED PRICE: 100 NGN for PRO upgrade
            # Backend enforces this price, frontend sends minimal data
            tx_ref = str(uuid.uuid4())

            with st.spinner("Generating payment link..."):

                # Call backend API
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/pay",
                        json={
                            "email": email,
                            "tx_ref": tx_ref
                        },
                        timeout=10
                    )
                    response.raise_for_status()
                    pay = response.json()
                except requests.exceptions.Timeout:
                    st.error("Backend request timed out. Please try again.")
                    st.stop()
                except requests.exceptions.ConnectionError:
                    st.error("Failed to connect to backend. Please check your internet connection.")
                    st.stop()
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to backend: {e}")
                    st.stop()
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    st.stop()

                if pay.get("status") == "success":
                    link = pay["data"]["link"]

                    st.success("Payment link created!")

                    st.markdown(f"👉 [Click here to pay]({link})")

                    st.info("After payment, your account will upgrade automatically. Click the button below to refresh your plan status.")

                    if st.button("🔄 Refresh Plan Status"):
                        try:
                            response = requests.get(f"{BACKEND_URL}/plan/{email}", timeout=10)
                            response.raise_for_status()
                            st.session_state.plan = response.json()["plan"]
                            st.rerun()
                        except requests.exceptions.Timeout:
                            st.error("Backend request timed out. Please try again.")
                        except requests.exceptions.ConnectionError:
                            st.error("Failed to connect to backend. Please check your internet connection.")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to refresh plan: {e}")
                        except Exception as e:
                            st.error(f"Unexpected error: {e}")

                else:
                    st.error(f"Payment failed: {pay.get('message', 'Unknown error')}")

    else:
        st.success("🎉 You are already PRO")