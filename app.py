import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib
import hmac
import streamlit as st
import pandas as pd

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "smartstock.db"

st.set_page_config(page_title="SmartStock", page_icon="📦", layout="wide")

# Demo-only accounts. Change these before sharing the project publicly.
DEMO_USERS = {
    "admin": {"password": "Admin@123", "role": "Admin", "name": "Demo Admin"},
    "manager": {"password": "Manager@123", "role": "Manager", "name": "Demo Manager"},
}

def password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, expected: str) -> bool:
    return hmac.compare_digest(password_hash(password), password_hash(expected))

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                supplier TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                reorder_level INTEGER NOT NULL DEFAULT 5,
                unit_price REAL NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                note TEXT,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            conn.executemany("""
                INSERT INTO products (sku, name, category, supplier, quantity, reorder_level, unit_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                ("SKU-1001", "A4 Paper Ream", "Stationery", "Paper House", 42, 10, 280),
                ("SKU-1002", "Whiteboard Marker", "Stationery", "Office Mart", 8, 12, 35),
                ("SKU-1003", "USB Keyboard", "Electronics", "Tech Supply", 15, 5, 650),
                ("SKU-1004", "Packing Tape", "Packaging", "PackRight", 4, 8, 75),
            ])

def query_df(sql, params=()):
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def add_transaction(product_id, product_name, action, quantity, note, username):
    with connect() as conn:
        conn.execute("""
            INSERT INTO transactions (product_id, product_name, action, quantity, note, username, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (product_id, product_name, action, quantity, note, username,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def login_screen():
    st.markdown("<h1 style='text-align:center'>📦 SmartStock</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:gray'>Inventory management solution</p>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.container(border=True):
            st.subheader("Sign in")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            if submitted:
                user = DEMO_USERS.get(username.strip().lower())
                if user and verify_password(password, user["password"]):
                    st.session_state["user"] = {
                        "username": username.strip().lower(),
                        "role": user["role"],
                        "name": user["name"],
                    }
                    st.rerun()
                st.error("Incorrect username or password.")
            with st.expander("Demo login credentials"):
                st.code("Admin:   admin / Admin@123\nManager: manager / Manager@123")
                
    

def main():
    init_db()
    if "user" not in st.session_state:
        login_screen()
        return

    user = st.session_state["user"]
    is_admin = user["role"] == "Admin"

    with st.sidebar:
        st.title("📦 SmartStock")
        st.caption("Inventory Management")
        st.divider()
        st.write(f"**{user['name']}**")
        st.caption(f"Role: {user['role']}")
        page = st.radio("Navigate", ["Dashboard", "Products", "Stock In / Out", "Transactions", "Reports"])
        if st.button("Log out", use_container_width=True):
            del st.session_state["user"]
            st.rerun()
        st.divider()
        

    st.title(page)
    st.caption("A simple inventory tracker for products, stock movements and low-stock monitoring.")

    products = query_df("SELECT * FROM products ORDER BY name")
    if page == "Dashboard":
        total_products = len(products)
        total_units = int(products["quantity"].sum()) if not products.empty else 0
        low_stock = int((products["quantity"] <= products["reorder_level"]).sum()) if not products.empty else 0
        inventory_value = float((products["quantity"] * products["unit_price"]).sum()) if not products.empty else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Products", total_products)
        c2.metric("Units in stock", f"{total_units:,}")
        c3.metric("Low-stock items", low_stock)
        c4.metric("Inventory value", f"₹{inventory_value:,.0f}")
        st.subheader("Low-stock alerts")
        low = products[products["quantity"] <= products["reorder_level"]]
        if low.empty:
            st.success("All products are above their reorder level.")
        else:
            st.dataframe(low[["sku", "name", "quantity", "reorder_level", "supplier"]], use_container_width=True, hide_index=True)
        st.subheader("Recently updated")
        recent = query_df("SELECT created_at, product_name, action, quantity, username FROM transactions ORDER BY id DESC LIMIT 5")
        if recent.empty:
            st.info("No stock movements yet. Add a product or record a stock movement to get started.")
        else:
            st.dataframe(recent, use_container_width=True, hide_index=True)

    elif page == "Products":
        st.subheader("Product catalogue")
        st.dataframe(products, use_container_width=True, hide_index=True)
        st.caption("Product creation, editing and deletion are available to Admin users.")
        if is_admin:
            with st.expander("➕ Add product"):
                with st.form("add_product"):
                    a, b = st.columns(2)
                    sku = a.text_input("SKU *")
                    name = b.text_input("Product name *")
                    category = a.text_input("Category")
                    supplier = b.text_input("Supplier")
                    quantity = a.number_input("Opening quantity", min_value=0, step=1)
                    reorder = b.number_input("Reorder level", min_value=0, value=5, step=1)
                    price = a.number_input("Unit price (₹)", min_value=0.0, step=10.0)
                    save = st.form_submit_button("Save product", type="primary")
                if save:
                    if not sku.strip() or not name.strip():
                        st.error("SKU and product name are required.")
                    else:
                        try:
                            with connect() as conn:
                                conn.execute("""
                                    INSERT INTO products (sku, name, category, supplier, quantity, reorder_level, unit_price)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (sku.strip(), name.strip(), category.strip(), supplier.strip(), int(quantity), int(reorder), float(price)))
                            st.success("Product added.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("That SKU already exists.")
            with st.expander("✏️ Edit or delete product"):
                if not products.empty:
                    selected_id = st.selectbox("Choose product", products["id"], format_func=lambda x: f"{products.loc[products.id == x, 'sku'].iloc[0]} — {products.loc[products.id == x, 'name'].iloc[0]}")
                    selected = products[products.id == selected_id].iloc[0]
                    with st.form("edit_product"):
                        name2 = st.text_input("Product name", value=selected["name"])
                        category2 = st.text_input("Category", value=selected["category"] or "")
                        supplier2 = st.text_input("Supplier", value=selected["supplier"] or "")
                        reorder2 = st.number_input("Reorder level", min_value=0, value=int(selected["reorder_level"]), step=1)
                        price2 = st.number_input("Unit price (₹)", min_value=0.0, value=float(selected["unit_price"]), step=10.0)
                        update = st.form_submit_button("Update product")
                    if update:
                        with connect() as conn:
                            conn.execute("UPDATE products SET name=?, category=?, supplier=?, reorder_level=?, unit_price=? WHERE id=?",
                                         (name2.strip(), category2.strip(), supplier2.strip(), int(reorder2), float(price2), int(selected_id)))
                        st.success("Product updated.")
                        st.rerun()
                    if st.button("Delete selected product", type="secondary"):
                        with connect() as conn:
                            conn.execute("DELETE FROM products WHERE id=?", (int(selected_id),))
                        st.warning("Product deleted.")
                        st.rerun()
        else:
            st.info("Manager access is view-only for the product catalogue.")

    elif page == "Stock In / Out":
        st.subheader("Record a stock movement")
        if products.empty:
            st.info("Add a product first.")
        else:
            with st.form("stock_movement"):
                chosen = st.selectbox("Product", products["id"], format_func=lambda x: f"{products.loc[products.id == x, 'sku'].iloc[0]} — {products.loc[products.id == x, 'name'].iloc[0]} (stock: {int(products.loc[products.id == x, 'quantity'].iloc[0])})")
                action = st.radio("Movement", ["Stock In", "Stock Out"], horizontal=True)
                qty = st.number_input("Quantity", min_value=1, step=1)
                note = st.text_input("Note (optional)")
                submit = st.form_submit_button("Record movement", type="primary")
            if submit:
                row = products[products.id == chosen].iloc[0]
                current = int(row["quantity"])
                if action == "Stock Out" and int(qty) > current:
                    st.error(f"Not enough stock. Current quantity: {current}.")
                else:
                    new_qty = current + int(qty) if action == "Stock In" else current - int(qty)
                    with connect() as conn:
                        conn.execute("UPDATE products SET quantity=? WHERE id=?", (new_qty, int(chosen)))
                    add_transaction(int(chosen), row["name"], action, int(qty), note.strip(), user["username"])
                    st.success(f"{action} recorded. New stock: {new_qty}.")
                    st.rerun()
        st.subheader("Current stock")
        st.dataframe(products[["sku", "name", "quantity", "reorder_level"]], use_container_width=True, hide_index=True)

    elif page == "Transactions":
        history = query_df("SELECT created_at, product_name, action, quantity, note, username FROM transactions ORDER BY id DESC")
        if history.empty:
            st.info("No transactions recorded yet.")
        else:
            st.dataframe(history, use_container_width=True, hide_index=True)

    elif page == "Reports":
        st.subheader("Inventory summary")
        report = products.copy()
        if not report.empty:
            report["stock_value"] = report["quantity"] * report["unit_price"]
            report["status"] = report.apply(lambda r: "Low stock" if r["quantity"] <= r["reorder_level"] else "In stock", axis=1)
            st.dataframe(report[["sku", "name", "category", "quantity", "reorder_level", "unit_price", "stock_value", "status"]], use_container_width=True, hide_index=True)
            st.download_button("Download inventory report (CSV)", report.to_csv(index=False).encode("utf-8"), "smartstock_inventory_report.csv", "text/csv")
            st.download_button("Download transaction history (CSV)",
                               query_df("SELECT * FROM transactions ORDER BY id DESC").to_csv(index=False).encode("utf-8"),
                               "smartstock_transactions.csv", "text/csv")
        else:
            st.info("No products available to report.")

    

if __name__ == "__main__":
    main()
