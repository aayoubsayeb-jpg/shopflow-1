import streamlit as st
import requests, os, time, json

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8000")

st.set_page_config(
    page_title="ShopZone — E-Commerce",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.main { background: #0f1117; }

.hero-banner {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid #2d3748;
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    margin-bottom: 24px;
}

.hero-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.hero-sub {
    color: #a0aec0;
    font-size: 1.1rem;
    margin-top: 8px;
}

.product-card {
    background: linear-gradient(145deg, #1a1f2e, #16213e);
    border: 1px solid #2d3748;
    border-radius: 16px;
    padding: 20px;
    transition: all 0.3s ease;
    height: 100%;
}

.product-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102,126,234,0.2);
}

.product-emoji {
    font-size: 3.5rem;
    text-align: center;
    display: block;
    margin-bottom: 12px;
}

.product-name {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    line-height: 1.3;
}

.product-category {
    color: #667eea;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 4px 0;
}

.product-price {
    color: #48bb78;
    font-size: 1.4rem;
    font-weight: 700;
    margin: 8px 0;
}

.product-desc {
    color: #718096;
    font-size: 0.8rem;
    line-height: 1.5;
    margin: 8px 0;
}

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    background: rgba(102,126,234,0.15);
    color: #667eea;
    border: 1px solid rgba(102,126,234,0.3);
}

.stat-card {
    background: linear-gradient(145deg, #1a1f2e, #16213e);
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}

.stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #667eea;
}

.stat-label {
    color: #718096;
    font-size: 0.85rem;
}

.cart-item {
    background: #1a1f2e;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 12px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.tracking-card {
    background: linear-gradient(145deg, #1a1f2e, #16213e);
    border: 1px solid #2d3748;
    border-radius: 16px;
    padding: 24px;
}

.status-step {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
}

.status-done { color: #48bb78; }
.status-active { color: #667eea; font-weight: 600; }
.status-pending { color: #4a5568; }

.rec-card {
    background: linear-gradient(145deg, #1a1f2e, #16213e);
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    transition: all 0.2s;
}

.rec-card:hover {
    border-color: #f093fb;
    box-shadow: 0 4px 15px rgba(240,147,251,0.15);
}

.success-banner {
    background: linear-gradient(135deg, #0d4f2e, #1a6b3c);
    border: 1px solid #48bb78;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
}

.auth-container {
    max-width: 420px;
    margin: 0 auto;
    background: linear-gradient(145deg, #1a1f2e, #16213e);
    border: 1px solid #2d3748;
    border-radius: 20px;
    padding: 40px;
}

[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #2d3748;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

div[data-testid="stMetric"] {
    background: #1a1f2e;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
for k, v in [("token",None),("user_id",None),("username",None),
             ("cart",[]),("page","home"),("selected_product",None),
             ("last_order",None),("last_payment",None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── API helpers ───────────────────────────────────────────────────────────────
def api(method, path, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        if st.session_state.token:
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        r = getattr(requests, method)(f"{GATEWAY}/{path}", headers=headers, timeout=10, **kwargs)
        return r
    except Exception as e:
        return None

def go(page):
    st.session_state.page = page
    st.rerun()

# ── AUTH PAGE ─────────────────────────────────────────────────────────────────
def page_auth():
    st.markdown("""
    <div style="text-align:center; padding: 20px 0;">
        <div style="font-size:4rem;">🛍️</div>
        <h1 style="color:#e2e8f0; font-size:2.5rem; margin:0;">ShopZone</h1>
        <p style="color:#718096;">Premium E-Commerce Platform</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1,2,1])[1]
    with col:
        tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "✨ حساب جديد"])

        with tab1:
            st.markdown("#### أهلاً بعودتك")
            uname = st.text_input("اسم المستخدم", key="li_u", placeholder="أدخل اسم المستخدم")
            pw    = st.text_input("كلمة المرور", type="password", key="li_p", placeholder="••••••••")
            if st.button("🚀 دخول", use_container_width=True, type="primary"):
                r = api("post", "auth/login", json={"username": uname, "password": pw})
                if r and r.status_code == 200:
                    d = r.json()
                    st.session_state.token    = d["token"]
                    st.session_state.user_id  = d["user_id"]
                    st.session_state.username = d["username"]
                    st.success("✅ مرحباً بك!")
                    time.sleep(0.5)
                    go("home")
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")

        with tab2:
            st.markdown("#### إنشاء حساب جديد")
            new_u = st.text_input("اسم المستخدم", key="reg_u", placeholder="اختر اسم مستخدم")
            new_e = st.text_input("البريد الإلكتروني", key="reg_e", placeholder="email@example.com")
            new_p = st.text_input("كلمة المرور", type="password", key="reg_p", placeholder="••••••••")
            new_p2= st.text_input("تأكيد كلمة المرور", type="password", key="reg_p2", placeholder="••••••••")
            if st.button("✨ إنشاء الحساب", use_container_width=True, type="primary"):
                if new_p != new_p2:
                    st.error("كلمتا المرور غير متطابقتين")
                elif len(new_p) < 6:
                    st.error("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                else:
                    r = api("post", "auth/register",
                            json={"username":new_u,"email":new_e,"password":new_p})
                    if r and r.status_code == 200:
                        d = r.json()
                        st.session_state.token    = d["token"]
                        st.session_state.user_id  = d["user_id"]
                        st.session_state.username = d["username"]
                        st.success("🎉 تم إنشاء حسابك بنجاح!")
                        time.sleep(0.5)
                        go("home")
                    elif r and r.status_code == 409:
                        st.error("اسم المستخدم أو البريد الإلكتروني موجود مسبقاً")
                    else:
                        st.error("حدث خطأ، حاول مرة أخرى")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:16px 0;">
            <div style="font-size:2.5rem;">🛍️</div>
            <h2 style="color:#e2e8f0; margin:4px 0;">ShopZone</h2>
            <p style="color:#667eea; font-size:0.85rem;">مرحباً، {st.session_state.username} 👋</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        pages = [
            ("🏠", "الرئيسية", "home"),
            ("🛒", f"السلة ({len(st.session_state.cart)})", "cart"),
            ("📦", "طلباتي", "orders"),
            ("🚚", "تتبع الطلبية", "tracking"),
        ]
        for icon, label, p in pages:
            active = st.session_state.page == p
            if st.button(f"{icon} {label}", use_container_width=True,
                         type="primary" if active else "secondary"):
                go(p)

        st.divider()

        cart_total = sum(i["price"]*i["qty"] for i in st.session_state.cart)
        if cart_total > 0:
            st.markdown(f"""
            <div class="stat-card">
                <div style="color:#a0aec0;font-size:0.8rem;">إجمالي السلة</div>
                <div style="color:#48bb78;font-size:1.5rem;font-weight:700;">${cart_total:.2f}</div>
                <div style="color:#718096;font-size:0.75rem;">{len(st.session_state.cart)} منتج</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            for k in ["token","user_id","username","cart","last_order","last_payment"]:
                st.session_state[k] = None if k != "cart" else []
            st.session_state.page = "auth"
            st.rerun()

# ── HOME PAGE ─────────────────────────────────────────────────────────────────
def page_home():
    st.markdown("""
    <div class="hero-banner">
        <p class="hero-title">🛍️ ShopZone</p>
        <p class="hero-sub">اكتشف أفضل المنتجات بأسعار لا تُقاوم</p>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    c1, c2, c3 = st.columns([2,2,1])
    with c1:
        search = st.text_input("🔍 ابحث عن منتج...", placeholder="iPhone, Nike, Sony...", label_visibility="collapsed")
    with c2:
        cats_r = api("get", "stock/categories")
        cats = ["الكل"] + (cats_r.json() if cats_r and cats_r.status_code==200 else [])
        cat = st.selectbox("الفئة", cats, label_visibility="collapsed")
    with c3:
        st.markdown("")

    # Fetch products
    params = {}
    if search: params["search"] = search
    if cat != "الكل": params["category"] = cat
    r = api("get", "stock/products", params=params)
    products = r.json() if r and r.status_code==200 else []

    if not products:
        st.info("لا توجد منتجات تطابق البحث")
        return

    st.markdown(f"<p style='color:#718096;'>عُثر على <b style='color:#667eea'>{len(products)}</b> منتج</p>", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, p in enumerate(products):
        with cols[i % 3]:
            tags = json.loads(p.get("tags","[]")) if isinstance(p.get("tags"), str) else []
            st.markdown(f"""
            <div class="product-card">
                <span class="product-emoji">{p.get('emoji','📦')}</span>
                <p class="product-category">{p['category']}</p>
                <p class="product-name">{p['name']}</p>
                <p class="product-price">${p['price']:.2f}</p>
                <p class="product-desc">{p.get('description','')[:80]}...</p>
                <p style="color:#718096;font-size:0.75rem;">📦 المخزون: {p['quantity']} وحدة</p>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            with b1:
                if st.button("🛒 للسلة", key=f"cart_{p['id']}", use_container_width=True):
                    existing = next((x for x in st.session_state.cart if x["id"]==p["id"]), None)
                    if existing:
                        existing["qty"] += 1
                    else:
                        st.session_state.cart.append({
                            "id": p["id"], "name": p["name"],
                            "price": p["price"], "emoji": p.get("emoji","📦"),
                            "qty": 1, "category": p["category"]
                        })
                    st.toast(f"✅ أُضيف {p['name']} للسلة")
            with b2:
                if st.button("⚡ اشتر", key=f"buy_{p['id']}", use_container_width=True, type="primary"):
                    st.session_state.selected_product = p
                    go("checkout")

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── CART PAGE ─────────────────────────────────────────────────────────────────
def page_cart():
    st.markdown("## 🛒 سلة التسوق")
    if not st.session_state.cart:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#718096;">
            <div style="font-size:4rem;">🛒</div>
            <h3>السلة فارغة</h3>
            <p>أضف بعض المنتجات للبدء</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏠 تصفح المنتجات", type="primary"):
            go("home")
        return

    total = 0
    for item in st.session_state.cart:
        c1, c2, c3, c4 = st.columns([1,3,2,1])
        with c1:
            st.markdown(f"<div style='font-size:2.5rem;text-align:center'>{item['emoji']}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{item['name']}**")
            st.caption(item['category'])
        with c3:
            q = st.number_input("الكمية", 1, 10, item["qty"], key=f"q_{item['id']}", label_visibility="collapsed")
            item["qty"] = q
            sub = item["price"] * q
            total += sub
            st.markdown(f"<span style='color:#48bb78;font-weight:600'>${sub:.2f}</span>", unsafe_allow_html=True)
        with c4:
            if st.button("🗑️", key=f"rm_{item['id']}"):
                st.session_state.cart = [x for x in st.session_state.cart if x["id"] != item["id"]]
                st.rerun()
        st.divider()

    col1, col2, col3 = st.columns([2,1,1])
    with col2:
        st.metric("الإجمالي", f"${total:.2f}")
    with col3:
        if st.button("💳 الدفع الآن", type="primary", use_container_width=True):
            if len(st.session_state.cart) == 1:
                st.session_state.selected_product = {
                    "id": st.session_state.cart[0]["id"],
                    "name": st.session_state.cart[0]["name"],
                    "price": total,
                }
            else:
                st.session_state.selected_product = {
                    "id": st.session_state.cart[0]["id"],
                    "name": f"{len(st.session_state.cart)} منتجات",
                    "price": total,
                }
            go("checkout")

# ── CHECKOUT PAGE ─────────────────────────────────────────────────────────────
def page_checkout():
    p = st.session_state.selected_product
    if not p:
        go("home"); return

    st.markdown("## 💳 إتمام الدفع")
    col1, col2 = st.columns([3,2])

    with col1:
        st.markdown("### معلومات البطاقة")
        st.markdown("""
        <div style="background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;padding:20px;margin-bottom:16px;">
            <p style="color:#718096;font-size:0.8rem;margin:0;">💡 للاختبار استخدم: 4532015112830366 | شهر 12 / سنة 26 | 123</p>
        </div>
        """, unsafe_allow_html=True)

        holder = st.text_input("اسم حامل البطاقة", placeholder="AHMED BENALI")

        # Card number: user types raw digits, we display spaced and strip for API
        raw_number = st.text_input("رقم البطاقة", placeholder="4532 0151 1283 0366", max_chars=19,
                                    key="card_number_input")
        # Strip spaces/dashes the user may have typed, then reformat 4-4-4-4
        digits_only = raw_number.replace(" ", "").replace("-", "")
        if digits_only:
            formatted = " ".join([digits_only[i:i+4] for i in range(0, min(len(digits_only),16), 4)])
            if formatted != raw_number:
                st.caption(f"→ {formatted}")

        # Expiry: real month/year dropdowns
        import datetime as _dt
        c1, c2, c3 = st.columns([2, 2, 2])
        current_year = _dt.datetime.now().year
        months = [f"{m:02d}" for m in range(1, 13)]
        years  = [str(y)[-2:] for y in range(current_year, current_year + 11)]
        with c1:
            exp_month = st.selectbox("الشهر", months, index=0)
        with c2:
            exp_year  = st.selectbox("السنة", years,  index=0)
        with c3:
            cvv = st.text_input("CVV", placeholder="123", max_chars=3, type="password")
        expiry = f"{exp_month}/{exp_year}"

    with col2:
        st.markdown("### ملخص الطلب")
        st.markdown(f"""
        <div style="background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;padding:20px;">
            <div style="font-size:2rem;text-align:center;margin-bottom:12px;">{p.get('emoji','📦')}</div>
            <p style="color:#e2e8f0;font-weight:600;">{p['name']}</p>
            <hr style="border-color:#2d3748">
            <div style="display:flex;justify-content:space-between;">
                <span style="color:#718096;">المجموع</span>
                <span style="color:#48bb78;font-size:1.3rem;font-weight:700;">${p['price']:.2f}</span>
            </div>
            <p style="color:#667eea;font-size:0.8rem;margin-top:12px;">🔒 الدفع مشفر ومؤمن</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    if st.button("✅ تأكيد الدفع", type="primary", use_container_width=True):
        if not all([holder, digits_only, cvv]):
            st.error("يرجى ملء جميع حقول البطاقة")
            return

        with st.spinner("جاري معالجة الدفع... 🏦"):
            # Create order
            order_r = api("post", "orders/create", json={
                "user_id": st.session_state.user_id,
                "product_id": p["id"],
                "product_name": p["name"],
                "quantity": 1,
                "total_price": p["price"]
            })
            if not order_r or order_r.status_code != 200:
                st.error("فشل في إنشاء الطلب"); return
            order_id = order_r.json()["order_id"]

            # Process payment (Javalin)
            pay_r = api("post", "payments/authorize", json={
                "card_number": digits_only,
                "expiry": expiry,
                "cvv": cvv,
                "card_holder": holder,
                "order_id": order_id,
                "user_id": st.session_state.user_id,
                "amount": p["price"]
            })

            # None means the request never reached the service (network/connection error)
            if pay_r is None:
                st.error("🔌 Payment service is unavailable — please try again later.")
                return

            # Guard against empty body (e.g. 500 with no JSON)
            try:
                pay_data = pay_r.json()
            except Exception:
                st.error(f"🔌 Payment service is unavailable — please try again later.")
                return

            if pay_r.status_code == 200 and pay_data.get("status") == "AUTHORIZED":
                # Confirm order
                api("post", f"orders/{order_id}/confirm-payment",
                    json={"payment_id": pay_data["payment_id"]})
                # Record purchase for ML
                api("post", "recommendations/record-purchase",
                    json={"user_id": st.session_state.user_id, "product_id": p["id"]})

                st.session_state.last_order   = order_id
                st.session_state.last_payment = pay_data["payment_id"]
                st.session_state.cart = []
                go("success")

            elif pay_r.status_code == 400:
                # Bad request = invalid card data (rejected before hitting the bank)
                st.error("❌ Invalid card details — please check your card number, expiry, and CVV.")

            elif pay_r.status_code == 402:
                # 402 = card valid but bank refused
                st.error("🏦 Card declined by bank — please try a different card.")

            else:
                # Unexpected error from the payment service
                msg = pay_data.get("message", "Payment failed")
                st.error(f"⚠️ Payment service error: {msg}")

# ── SUCCESS PAGE ───────────────────────────────────────────────────────────────
def page_success():
    order_id = st.session_state.last_order
    p = st.session_state.selected_product

    st.markdown(f"""
    <div class="success-banner">
        <div style="font-size:4rem;">🎉</div>
        <h2 style="color:#48bb78;margin:8px 0;">تم الدفع بنجاح!</h2>
        <p style="color:#9ae6b4;">رقم الطلب: <b>{order_id}</b></p>
        <p style="color:#9ae6b4;">رقم الدفع: <b>{st.session_state.last_payment}</b></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # Get delivery tracking
    if order_id:
        time.sleep(1)
        del_r = api("get", f"delivery/order/{order_id}")
        if del_r and del_r.status_code == 200:
            dd = del_r.json()
            st.markdown(f"""
            <div style="background:#1a1f2e;border:1px solid #667eea;border-radius:12px;padding:20px;text-align:center;">
                <h3 style="color:#667eea;">🚚 رقم التتبع الخاص بك</h3>
                <div style="font-size:2rem;font-weight:700;color:#e2e8f0;letter-spacing:2px;">{dd.get('tracking_number','')}</div>
                <p style="color:#718096;">احفظ هذا الرقم لتتبع طلبيتك من قسم التتبع</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💡 قد يعجبك أيضاً")

    if p:
        rec_r = api("get", f"recommendations/for-product/{p['id']}",
                    params={"user_id": st.session_state.user_id})
        if rec_r and rec_r.status_code == 200:
            recs = rec_r.json().get("recommendations", [])
            if recs:
                cols = st.columns(min(len(recs), 3))
                for i, rec in enumerate(recs[:3]):
                    with cols[i]:
                        st.markdown(f"""
                        <div class="rec-card">
                            <div style="font-size:2.5rem;">{rec.get('emoji','📦')}</div>
                            <p style="color:#e2e8f0;font-weight:600;font-size:0.9rem;">{rec['name']}</p>
                            <p style="color:#48bb78;font-weight:700;">${rec['price']:.2f}</p>
                            <p style="color:#718096;font-size:0.75rem;">{rec.get('reason','')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("اشتري الآن", key=f"rec_{rec['product_id']}", use_container_width=True):
                            st.session_state.selected_product = rec
                            st.session_state.selected_product["id"] = rec["product_id"]
                            go("checkout")

    st.markdown("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏠 العودة للرئيسية", use_container_width=True, type="primary"):
            go("home")
    with c2:
        if st.button("🚚 تتبع الطلبية", use_container_width=True):
            go("tracking")

# ── TRACKING PAGE ─────────────────────────────────────────────────────────────
def page_tracking():
    st.markdown("## 🚚 تتبع الطلبية")

    tracking_num = st.text_input("أدخل رقم التتبع",
                                  placeholder="TRK-XXXXXXXX",
                                  value=st.session_state.get("prefill_tracking",""))

    if st.button("🔍 تتبع", type="primary", use_container_width=True):
        if not tracking_num:
            st.error("أدخل رقم التتبع"); return

        with st.spinner("جاري البحث..."):
            r = api("get", f"delivery/track/{tracking_num.strip().upper()}")

        if not r or r.status_code == 404:
            st.error("❌ رقم التتبع غير موجود"); return

        d = r.json()
        status = d.get("status","")
        progress = d.get("progress_pct", 0)

        # Status header
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a1f2e,#16213e);border:1px solid #667eea;
                    border-radius:16px;padding:24px;text-align:center;margin-bottom:20px;">
            <div style="font-size:3rem;">{d.get('status_label','🚚').split()[0]}</div>
            <h2 style="color:#e2e8f0;">{d.get('status_label','')}</h2>
            <p style="color:#667eea;font-size:1.1rem;">طلب: {d.get('order_id','')} | {d.get('product_name','')}</p>
            <p style="color:#718096;">الوجهة: 📍 {d.get('dest_name','')} | الوقت المقدر: ⏱️ {d.get('eta_minutes',0)} دقيقة</p>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar
        st.markdown("#### مسار التوصيل")
        st.progress(int(progress))
        st.markdown(f"<p style='color:#667eea;text-align:center;font-weight:600'>{progress:.1f}% مكتمل</p>", unsafe_allow_html=True)

        # Status steps
        steps = [
            ("WAREHOUSE",        "📦", "في المستودع"),
            ("PICKED_UP",        "🚛", "تم الاستلام"),
            ("IN_TRANSIT",       "🚚", "في الطريق"),
            ("OUT_FOR_DELIVERY", "🏃", "خارج للتوصيل"),
            ("DELIVERED",        "✅", "تم التوصيل"),
        ]
        status_order = [s[0] for s in steps]
        current_idx  = status_order.index(status) if status in status_order else 0
        cols = st.columns(len(steps))
        for i, (s, icon, label) in enumerate(steps):
            with cols[i]:
                if i < current_idx:
                    color, border = "#48bb78", "2px solid #48bb78"
                elif i == current_idx:
                    color, border = "#667eea", "2px solid #667eea"
                else:
                    color, border = "#4a5568", "1px solid #2d3748"
                st.markdown(f"""
                <div style="text-align:center;padding:12px 4px;border:{border};
                            border-radius:10px;background:#1a1f2e;">
                    <div style="font-size:1.5rem;">{icon}</div>
                    <div style="color:{color};font-size:0.7rem;font-weight:600;margin-top:4px;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        # Map
        st.markdown("---")
        st.markdown("#### 📍 الموقع الحالي على الخريطة")
        lat = d.get("current_lat"); lng = d.get("current_lng")
        dest_lat = d.get("dest_lat"); dest_lng = d.get("dest_lng")
        wh = d.get("warehouse", {})

        if lat and lng:
            map_url = (
                f"https://maps.google.com/maps?q={lat},{lng}"
                f"&z=13&output=embed"
            )
            st.markdown(f"""
            <div style="border:1px solid #2d3748;border-radius:12px;overflow:hidden;">
                <iframe width="100%" height="400"
                    src="{map_url}"
                    frameborder="0" allowfullscreen
                    style="display:block">
                </iframe>
            </div>
            <p style="color:#718096;font-size:0.8rem;text-align:center;margin-top:8px;">
                📍 الموقع الحالي: {lat:.4f}, {lng:.4f} &nbsp;|&nbsp;
                🏁 الوجهة: {d.get('dest_name','')} ({dest_lat:.4f}, {dest_lng:.4f})
            </p>
            """, unsafe_allow_html=True)

            g_maps_url = f"https://www.google.com/maps/dir/{wh.get('lat',0)},{wh.get('lng',0)}/{dest_lat},{dest_lng}"
            st.markdown(f"""
            <div style="text-align:center;margin-top:12px;">
                <a href="{g_maps_url}" target="_blank"
                   style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;
                          padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;">
                    🗺️ فتح في Google Maps
                </a>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🔄 تحديث الموقع", use_container_width=True):
            st.rerun()

# ── ORDERS PAGE ───────────────────────────────────────────────────────────────
def page_orders():
    st.markdown("## 📦 طلباتي")
    r = api("get", f"orders/user/{st.session_state.user_id}")
    if not r or r.status_code != 200:
        st.error("تعذر جلب الطلبات"); return

    orders = r.json()
    if not orders:
        st.info("لا توجد طلبات حتى الآن. ابدأ التسوق!")
        if st.button("🛍️ تسوق الآن", type="primary"): go("home")
        return

    status_color = {"PENDING":"#f6ad55","PAID":"#48bb78","SHIPPED":"#667eea"}
    for o in orders:
        color = status_color.get(o["status"],"#718096")
        c1, c2, c3 = st.columns([3,2,1])
        with c1:
            st.markdown(f"**{o.get('product_name','منتج')}**")
            st.caption(f"رقم الطلب: {o['id']} • {o['created'][:10]}")
        with c2:
            st.markdown(f"<span style='color:{color};font-weight:600'>{o['status']}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#48bb78;font-weight:700'>${o['total_price']:.2f}</span>", unsafe_allow_html=True)
        with c3:
            if o.get("delivery_id"):
                del_r = api("get", f"delivery/order/{o['id']}")
                if del_r and del_r.status_code == 200:
                    tn = del_r.json().get("tracking_number","")
                    if st.button("🚚 تتبع", key=f"tr_{o['id']}"):
                        st.session_state.prefill_tracking = tn
                        go("tracking")
        st.divider()

# ── ROUTER ────────────────────────────────────────────────────────────────────
if not st.session_state.token:
    page_auth()
else:
    render_sidebar()
    page = st.session_state.page
    if   page == "home":     page_home()
    elif page == "cart":     page_cart()
    elif page == "checkout": page_checkout()
    elif page == "success":  page_success()
    elif page == "tracking": page_tracking()
    elif page == "orders":   page_orders()
    else: page_home()
