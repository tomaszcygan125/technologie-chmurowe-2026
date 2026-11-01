import os
import pymysql
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "wms-secret"


def get_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "wms"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def place_order(product_id, qty):
    """Returns (ok, message, order_id). The entire operation is one transaction."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Lock material rows (ORDER BY id => avoids deadlocks)
            cur.execute(
                """SELECT m.id, m.name, m.quantity,
                          pm.quantity_required * %s AS needed
                   FROM product_materials pm
                   JOIN materials m ON m.id = pm.material_id
                   WHERE pm.product_id = %s
                   ORDER BY m.id
                   FOR UPDATE OF m""",
                (qty, product_id),
            )
            rows = cur.fetchall()
            if not rows:
                conn.rollback()
                return False, "Product does not exist or has no recipe", None

            missing = [f"{r['name']} (needed {r['needed']}, available {r['quantity']})"
                       for r in rows if r["quantity"] < r["needed"]]
            if missing:
                conn.rollback()
                return False, "Missing materials: " + "; ".join(missing), None

            cur.execute(
                "INSERT INTO orders (product_id, quantity, status) VALUES (%s,%s,'COMPLETED')",
                (product_id, qty),
            )
            order_id = cur.lastrowid
            for r in rows:
                cur.execute("UPDATE materials SET quantity = quantity - %s WHERE id = %s",
                            (r["needed"], r["id"]))
                cur.execute(
                    "INSERT INTO stock_history (material_id, order_id, quantity_change) VALUES (%s,%s,%s)",
                    (r["id"], order_id, -r["needed"]),
                )
        conn.commit()
        return True, "Order accepted", order_id
    except Exception as e:
        conn.rollback()
        return False, f"Error: {e}", None
    finally:
        conn.close()


def query(sql, args=None):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()
    finally:
        conn.close()


PAGE = """
<!doctype html><html lang="pl"><head><meta charset="utf-8">
<title>WMS</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="container py-4">
<h1>Warehouse Management System</h1>
{% with msgs = get_flashed_messages(with_categories=true) %}
  {% for cat, m in msgs %}<div class="alert alert-{{cat}}">{{m}}</div>{% endfor %}
{% endwith %}
<h3 class="mt-4">New order</h3>
<form method="post" action="/order" class="row g-2">
  <div class="col-auto"><select name="product_id" class="form-select">
    {% for p in products %}<option value="{{p.id}}">{{p.name}}</option>{% endfor %}
  </select></div>
  <div class="col-auto"><input type="number" name="quantity" value="1" min="1" class="form-control"></div>
  <div class="col-auto"><button class="btn btn-primary">Order</button></div>
</form>
<h3 class="mt-4">Inventory levels</h3>
<table class="table table-sm table-striped"><tr><th>ID</th><th>Material</th><th>Quantity</th><th>Minimum</th></tr>
{% for m in materials %}<tr class="{{'table-danger' if m.quantity < m.minimum_quantity}}">
<td>{{m.id}}</td><td>{{m.name}}</td><td>{{m.quantity}}</td><td>{{m.minimum_quantity}}</td></tr>{% endfor %}
</table>
<h3 class="mt-4">Recent orders</h3>
<table class="table table-sm"><tr><th>ID</th><th>Product</th><th>Quantity</th><th>Status</th><th>Date</th></tr>
{% for o in orders %}<tr><td>{{o.id}}</td><td>{{o.name}}</td><td>{{o.quantity}}</td><td>{{o.status}}</td><td>{{o.created_at}}</td></tr>{% endfor %}
</table>
<h3 class="mt-4">Stock history (last 15)</h3>
<table class="table table-sm"><tr><th>ID</th><th>Material</th><th>Order</th><th>Change</th><th>Date</th></tr>
{% for h in history %}<tr><td>{{h.id}}</td><td>{{h.name}}</td><td>{{h.order_id}}</td><td>{{h.quantity_change}}</td><td>{{h.created_at}}</td></tr>{% endfor %}
</table>
</body></html>
"""


@app.route("/")
def index():
    return render_template_string(
        PAGE,
        products=query("SELECT id, name FROM products"),
        materials=query("SELECT * FROM materials ORDER BY id"),
        orders=query("""SELECT o.id, p.name, o.quantity, o.status, o.created_at
                        FROM orders o JOIN products p ON p.id=o.product_id
                        ORDER BY o.id DESC LIMIT 10"""),
        history=query("""SELECT h.id, m.name, h.order_id, h.quantity_change, h.created_at
                         FROM stock_history h JOIN materials m ON m.id=h.material_id
                         ORDER BY h.id DESC LIMIT 15"""),
    )


@app.route("/order", methods=["POST"])
def order_form():
    ok, msg, oid = place_order(int(request.form["product_id"]), int(request.form["quantity"]))
    flash(msg + (f" (no. {oid})" if oid else ""), "success" if ok else "danger")
    return redirect(url_for("index"))


@app.route("/api/order", methods=["POST"])
def order_api():
    data = request.get_json(force=True)
    ok, msg, oid = place_order(int(data["product_id"]), int(data["quantity"]))
    return jsonify({"ok": ok, "message": msg, "order_id": oid}), (200 if ok else 409)


@app.route("/api/materials")
def materials_api():
    return jsonify(query("SELECT id, name, quantity FROM materials ORDER BY id"))


@app.route("/health")
def health():
    return "ok"