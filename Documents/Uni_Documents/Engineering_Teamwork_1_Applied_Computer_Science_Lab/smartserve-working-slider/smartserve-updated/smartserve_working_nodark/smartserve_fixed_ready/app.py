from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = "smartserve-secret"

# Load users from JSON
with open("users.json") as f:
    user_data = json.load(f)

employees = user_data["employees"]
cooks = user_data["cooks"]
managers = user_data["managers"]

# Load inventory from JSON
def load_inventory():
    with open("inventory.json") as f:
        return json.load(f)

def save_inventory(inv):
    with open("inventory.json", "w") as f:
        json.dump(inv, f, indent=2)

inventory = load_inventory()

# Initialize data structures
tables = {str(i): None for i in range(1, 11)}
orders = {}
employee_shifts = []
cook_shifts = []
waiting_list = []

@app.route("/")
def home():
    return render_template("base.html", content="""
        <div style="max-width: 500px; margin: 0 auto; padding: 20px; text-align: center;">
            <h1 style="color: #2c3e50; margin-bottom: 30px;">SmartServe</h1>
            <h3 style="color: #7f8c8d; margin-bottom: 25px;">Restaurant Management System</h3>
            
            <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin-bottom: 20px; color: #2c3e50;">Select Your Role</h4>
                
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    <a href='/login/employee' style="
                        display: block;
                        padding: 12px;
                        background: #3498db;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-weight: 500;
                        transition: background 0.3s;
                    ">Employee Login</a>
                    
                    <a href='/login/cook' style="
                        display: block;
                        padding: 12px;
                        background: #e67e22;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-weight: 500;
                        transition: background 0.3s;
                    ">Cook Login</a>
                    
                    <a href='/login/manager' style="
                        display: block;
                        padding: 12px;
                        background: #2ecc71;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-weight: 500;
                        transition: background 0.3s;
                    ">Manager Login</a>
                </div>
            </div>
        </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect("/")

# Login routes
def role_login_page(role, user_list):
    if request.method == "POST":
        name = request.form["name"]
        session["user"] = name
        session["role"] = role
        now = datetime.now()
        if role == "employee":
            employee_shifts.append({"name": name, "check_in": now, "check_out": None})
            return redirect("/employee")
        elif role == "cook":
            cook_shifts.append({"name": name, "check_in": now, "check_out": None})
            return redirect("/cook")
        elif role == "manager":
            return redirect("/manager")
    options = "".join(f"<option value='{name}'>{name}</option>" for name in user_list)
    return render_template("base.html", content=f"""
        <div style="max-width: 400px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50; margin-bottom: 20px; text-align: center;">{role.title()} Login</h2>
            <form method='post' style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <div style="margin-bottom: 15px;">
                    <select name='name' style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                        {options}
                    </select>
                </div>
                <button type='submit' style="
                    width: 100%;
                    padding: 10px;
                    background: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: 500;
                    cursor: pointer;
                ">Login</button>
            </form>
        </div>
    """)

@app.route("/login/employee", methods=["GET", "POST"])
def login_employee():
    return role_login_page("employee", employees)

@app.route("/login/cook", methods=["GET", "POST"])
def login_cook():
    return role_login_page("cook", cooks)

@app.route("/login/manager", methods=["GET", "POST"])
def login_manager():
    return role_login_page("manager", managers)

# Employee routes
@app.route("/employee")
def employee_dashboard():
    if session.get("role") != "employee":
        return redirect("/")

    name = session["user"]
    inv = load_inventory()
    
    # Table status
    table_rows = ""
    for t, v in tables.items():
        status = "FREE" if v is None else f"{v['customer']} ({v['count']} guests)"
        table_rows += f"<tr><td>{t}</td><td>{status}</td></tr>"
    
    # Waiting list
    wait_rows = "".join(f"<tr><td>{n}</td><td>{t.strftime('%H:%M')}</td></tr>" for n, t in waiting_list)
    
    # Ready orders
    ready_orders = ""
    for t, ol in orders.items():
        for idx, o in enumerate(ol):
            if o["ready"] and not o["delivered"]:
                ready_orders += f"""
                <tr>
                    <td>Table {t}</td>
                    <td>{', '.join(o['items'])}</td>
                    <td><a href='/deliver/{t}/{idx}' style="
                        display: inline-block;
                        padding: 5px 10px;
                        background: #2ecc71;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-size: 14px;
                    ">Mark Delivered</a></td>
                </tr>
                """
    
    # Menu options
    menu_opts = "".join(f"<option value='{item}'>${inv[item]['price']:.2f} - {item}</option>" for item in inv)

    content = f"""
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 style="color: #2c3e50;">Employee Dashboard - {name}</h2>
            <a href="/logout" style="
                padding: 8px 15px;
                background: #e74c3c;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            ">Logout</a>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Reserve Table</h3>
                <form method='post' action='/reserve'>
                    <div style="margin-bottom: 10px;">
                        <input name='customer' placeholder="Customer Name" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <input name='count' type='number' placeholder="Number of Guests" min='1' required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <button type='submit' style="
                        width: 100%;
                        padding: 10px;
                        background: #3498db;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Reserve Table</button>
                </form>
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Clear Tables</h3>
                <form method='post' action='/clear' style="margin-bottom: 15px;">
                    <button type='submit' style="
                        width: 100%;
                        padding: 10px;
                        background: #e74c3c;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Clear All Tables</button>
                </form>
                <form method='post' action='/clear-one'>
                    <div style="margin-bottom: 10px;">
                        <input name='table' placeholder="Table Number" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <button type='submit' style="
                        width: 100%;
                        padding: 10px;
                        background: #f39c12;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Clear Specific Table</button>
                </form>
            </div>
        </div>

        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Table Status</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Table</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Waiting List</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Name</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Time Added</th>
                        </tr>
                    </thead>
                    <tbody>
                        {wait_rows or '<tr><td colspan="2" style="padding: 10px; text-align: center;">Empty</td></tr>'}
                    </tbody>
                </table>
                <form method='post' action='/remove-waiting' style="margin-top: 15px;">
                    <div style="margin-bottom: 10px;">
                        <input name='remove_name' placeholder="Customer Name to Remove" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <button type='submit' style="
                        width: 100%;
                        padding: 10px;
                        background: #f39c12;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Remove from Waiting List</button>
                </form>
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Place Order</h3>
                <form method='post' action='/order'>
                    <div style="margin-bottom: 10px;">
                        <input name='table' placeholder="Table Number" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <select name='item' required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            {menu_opts}
                        </select>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <input name='qty' type='number' placeholder="Quantity" min='1' required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <button type='submit' style="
                        width: 100%;
                        padding: 10px;
                        background: #3498db;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Place Order</button>
                </form>
            </div>
        </div>

        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Ready Orders</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Table</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Items</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {ready_orders or '<tr><td colspan="3" style="padding: 10px; text-align: center;">No ready orders</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template("base.html", content=content)

@app.route("/reserve", methods=["POST"])
def reserve():
    if session.get("role") != "employee":
        return redirect("/")
    
    name = request.form["customer"].strip().title()
    count = int(request.form["count"])
    for t, v in tables.items():
        if v is None:
            tables[t] = {"customer": name, "time": datetime.now(), "count": count}
            flash(f"{name} reserved table {t}")
            return redirect("/employee")
    waiting_list.append((name, datetime.now()))
    flash(f"No free tables. {name} added to waiting list.")
    return redirect("/employee")

@app.route("/clear", methods=["POST"])
def clear_all():
    if session.get("role") != "employee":
        return redirect("/")
    
    for t in tables:
        tables[t] = None
    flash("All tables cleared.")
    return redirect("/employee")

@app.route("/clear-one", methods=["POST"])
def clear_one():
    if session.get("role") != "employee":
        return redirect("/")
    
    table = request.form["table"].strip()
    if table in tables:
        tables[table] = None
        flash(f"Table {table} cleared.")
    else:
        flash("Invalid table number.")
    return redirect("/employee")

@app.route("/remove-waiting", methods=["POST"])
def remove_waiting():
    if session.get("role") != "employee":
        return redirect("/")
    
    name = request.form["remove_name"].strip().title()
    for i, (n, _) in enumerate(waiting_list):
        if n == name:
            del waiting_list[i]
            flash(f"{name} removed from waiting list.")
            break
    else:
        flash(f"{name} not found.")
    return redirect("/employee")

@app.route("/order", methods=["POST"])
def place_order():
    if session.get("role") != "employee":
        return redirect("/")
    
    t = request.form["table"]
    item = request.form["item"]
    qty = int(request.form["qty"])

    inv = load_inventory()

    if inv[item]["stock"] < qty:
        flash(f"Not enough {item} in stock.")
        return redirect("/employee")

    inv[item]["stock"] -= qty
    save_inventory(inv)

    total = inv[item]["price"] * qty
    if t not in orders:
        orders[t] = []
    orders[t].append({
        "timestamp": datetime.now(),
        "items": [f"{item} x{qty}"],
        "total": total,
        "ready": False,
        "delivered": False
    })
    flash(f"Order placed for Table {t}: {item} x{qty}")
    return redirect("/employee")

@app.route("/deliver/<table>/<int:idx>")
def mark_delivered(table, idx):
    if session.get("role") != "employee":
        return redirect("/")
    
    if table in orders and 0 <= idx < len(orders[table]):
        orders[table][idx]["delivered"] = True
        flash(f"Order delivered to Table {table}.")
    return redirect("/employee")

# Cook routes
@app.route("/cook")
def cook_dashboard():
    if session.get("role") != "cook":
        return redirect("/")

    name = session["user"]
    pending_orders = ""
    for t, olist in orders.items():
        for i, o in enumerate(olist):
            if not o["ready"]:
                pending_orders += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">Table {t}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{', '.join(o['items'])}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{o['timestamp'].strftime('%H:%M')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <a href='/cook/ready/{t}/{i}' style="
                            display: inline-block;
                            padding: 5px 10px;
                            background: #2ecc71;
                            color: white;
                            text-decoration: none;
                            border-radius: 4px;
                        ">Mark Ready</a>
                    </td>
                </tr>
                """

    content = f"""
    <div style="max-width: 1000px; margin: 0 auto; padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 style="color: #2c3e50;">Cook Dashboard - {name}</h2>
            <a href="/logout" style="
                padding: 8px 15px;
                background: #e74c3c;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            ">Logout</a>
        </div>

        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Pending Orders</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Table</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Items</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Time Placed</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {pending_orders or '<tr><td colspan="4" style="padding: 10px; text-align: center;">No pending orders</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template("base.html", content=content)

@app.route("/cook/ready/<table>/<int:idx>")
def mark_ready(table, idx):
    if session.get("role") != "cook":
        return redirect("/")
    
    if table in orders and 0 <= idx < len(orders[table]):
        orders[table][idx]["ready"] = True
        flash(f"Order for Table {table} marked ready.")
    return redirect("/cook")

# Manager routes
@app.route("/manager", methods=["GET", "POST"])
def manager():
    if session.get("role") != "manager":
        return redirect("/")

    # Staff management
    active_staff = [f"{s['name']} (since {s['check_in'].strftime('%H:%M')})" 
                   for s in employee_shifts if s["check_out"] is None]
    
    active_cooks = [f"{s['name']} (since {s['check_in'].strftime('%H:%M')})" 
                   for s in cook_shifts if s["check_out"] is None]
    
    # Order summary
    order_summary = ""
    for t, ol in orders.items():
        for o in ol:
            status = "pending" if not o["ready"] else "ready" if not o["delivered"] else "delivered"
            status_bg = "#fff3cd" if status == "pending" else "#d4edda" if status == "ready" else "#d1ecf1"
            status_color = "#856404" if status == "pending" else "#155724" if status == "ready" else "#0c5460"
            order_summary += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">Table {t}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{', '.join(o['items'])}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">${o['total']:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{o['timestamp'].strftime('%H:%M')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <span style="
                        display: inline-block;
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: 500;
                        background: {status_bg};
                        color: {status_color};
                    ">{status.title()}</span>
                </td>
            </tr>
            """

    # Inventory management
    inv = load_inventory()
    inventory_rows = ""
    for item in inv:
        inventory_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{item}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <input name='price_{item}' value='{inv[item]['price']}' type='number' step='0.01' min='0' style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <input name='stock_{item}' value='{inv[item]['stock']}' type='number' min='0' style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            </td>
        </tr>
        """

    if request.method == "POST":
        for item in inv:
            try:
                inv[item]["price"] = float(request.form[f"price_{item}"])
                inv[item]["stock"] = int(request.form[f"stock_{item}"])
            except:
                continue
        save_inventory(inv)
        flash("Inventory updated successfully", "success")
        return redirect("/manager")

    content = f"""
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 style="color: #2c3e50;">Manager Dashboard</h2>
            <a href="/logout" style="
                padding: 8px 15px;
                background: #e74c3c;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            ">Logout</a>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Active Employees</h3>
                <ul style="list-style: none;">
                    {''.join(f'<li style="padding: 10px 0; border-bottom: 1px solid #eee;">{s}</li>' for s in active_staff) or '<li style="padding: 10px 0;">None</li>'}
                </ul>
            </div>

            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Active Cooks</h3>
                <ul style="list-style: none;">
                    {''.join(f'<li style="padding: 10px 0; border-bottom: 1px solid #eee;">{c}</li>' for c in active_cooks) or '<li style="padding: 10px 0;">None</li>'}
                </ul>
            </div>
        </div>

        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Current Orders</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Table</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Items</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Total</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Time</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {order_summary or '<tr><td colspan="5" style="padding: 10px; text-align: center;">No orders</td></tr>'}
                </tbody>
            </table>
        </div>

        <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="color: #2c3e50; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">Inventory Management</h3>
            <form method='post'>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Item</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Price ($)</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Stock</th>
                        </tr>
                    </thead>
                    <tbody>
                        {inventory_rows}
                    </tbody>
                </table>
                <button type='submit' style="
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                ">Update Inventory</button>
            </form>
        </div>
    </div>
    """
    return render_template("base.html", content=content)

if __name__ == "__main__":
    app.run(debug=True)