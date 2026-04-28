from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'ural_secret_key_2024'

# ─── ГЛАВНАЯ ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', active='home')

# ─── КОМПАНИЯ ──────────────────────────────────────────────────────────────────
@app.route('/company/')
def company_about():
    return render_template('company/about.html', active='company')

@app.route('/company/history/')
def company_history():
    return render_template('company/history.html', active='company')

@app.route('/company/documents/')
def company_documents():
    return render_template('company/documents.html', active='company')

@app.route('/company/partners/')
def company_partners():
    return render_template('company/partners.html', active='company')

@app.route('/company/reviews/')
def company_reviews():
    return render_template('company/reviews.html', active='company')

@app.route('/company/vacancies/')
def company_vacancies():
    return render_template('company/vacancies.html', active='company')

@app.route('/company/requisites/')
def company_requisites():
    return render_template('company/requisites.html', active='company')

# ─── КАТАЛОГ ───────────────────────────────────────────────────────────────────
@app.route('/catalog/')
def catalog_index():
    return render_template('catalog/index.html', active='catalog')

@app.route('/catalog/pullers/')
def catalog_pullers():
    return render_template('catalog/pullers.html', active='catalog')

@app.route('/catalog/couplings/')
def catalog_couplings():
    return render_template('catalog/couplings.html', active='catalog')

@app.route('/catalog/railway/')
def catalog_railway():
    return render_template('catalog/railway.html', active='catalog')

# ─── УСЛУГИ ────────────────────────────────────────────────────────────────────
@app.route('/services/')
def services_index():
    return render_template('services/index.html', active='services')

@app.route('/services/metalworking/')
def services_metalworking():
    return render_template('services/metalworking.html', active='services')

# ─── ИНФОРМАЦИЯ ────────────────────────────────────────────────────────────────
@app.route('/info/')
def info_index():
    return render_template('info/index.html', active='info')

@app.route('/info/news/')
def info_news():
    return render_template('info/news.html', active='info')

@app.route('/info/articles/')
def info_articles():
    return render_template('info/articles.html', active='info')

@app.route('/info/faq/')
def info_faq():
    return render_template('info/faq.html', active='info')

@app.route('/info/agreement/')
def info_agreement():
    return render_template('info/agreement.html', active='info')

# ─── КОНТАКТЫ ──────────────────────────────────────────────────────────────────
@app.route('/contacts/')
def contacts():
    return render_template('contacts.html', active='contacts')

@app.route('/contacts/submit', methods=['POST'])
def contacts_submit():
    name    = request.form.get('name', '').strip()
    email   = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()
    if name and email and message:
        flash('Ваше сообщение отправлено. Мы свяжемся с вами в ближайшее время.', 'success')
    else:
        flash('Пожалуйста, заполните все поля формы.', 'error')
    return redirect(url_for('contacts'))

# ─── БАЗА ДАННЫХ И АДМИН-ПАНЕЛЬ ───────────────────────────────────────────────
DATABASE = 'site.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            published_at TEXT,
            is_published INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            material TEXT,
            weight TEXT,
            in_stock INTEGER DEFAULT 1,
            is_published INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    """)

    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin12345"))
        )

    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO categories (name, description, sort_order) VALUES (?, ?, ?)",
            [
                ("Съёмники", "Специализированный инструмент для обслуживания пассажирских вагонов.", 1),
                ("Муфты", "Муфты и узлы для железнодорожного оборудования.", 2),
                ("ЖД Запчасти", "Детали и комплектующие для пассажирских вагонов.", 3),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM news")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO news (title, content, published_at) VALUES (?, ?, ?)",
            [
                ("У нас появился обновлённый сайт", "Представлен обновлённый сайт ЗАО ПП «Урал» с каталогом продукции и информационными разделами.", "2026-03-01"),
                ("Расширение производственных возможностей", "Предприятие продолжает развивать производственную базу и направления металлообработки.", "2025-12-01"),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO products (category_id, name, description, material, weight) VALUES (?, ?, ?, ?, ?)",
            [
                (1, "Съёмник «СМУГ»", "Съёмник муфты упругой гибкой для обслуживания пассажирских вагонов.", "Сталь 45", "по ТД"),
                (2, "Муфта МППГ-02", "Муфта предохранительная для генератора пассажирского вагона.", "Сталь", "по ТД"),
                (3, "Гайка со стопорным кожухом", "Комплектующая деталь для узлов пассажирских вагонов.", "Сталь", "по ТД"),
            ]
        )

    conn.commit()
    conn.close()

@app.before_request
def prepare_database():
    init_db()

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/admin/')
def admin_index():
    if session.get('admin_id'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/login/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            flash('Вы вошли в административную панель.', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Неверный логин или пароль.', 'error')

    return render_template('admin/login.html')

@app.route('/admin/logout/')
@login_required
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard/')
@login_required
def admin_dashboard():
    conn = get_db()
    stats = {
        "news": conn.execute("SELECT COUNT(*) FROM news").fetchone()[0],
        "categories": conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
        "products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
    }
    conn.close()
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/news/')
@login_required
def admin_news():
    conn = get_db()
    items = conn.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin/news.html', items=items)

@app.route('/admin/news/add/', methods=['GET', 'POST'])
@login_required
def admin_news_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        published_at = request.form.get('published_at', '').strip() or datetime.now().strftime('%Y-%m-%d')
        if title and content:
            conn = get_db()
            conn.execute("INSERT INTO news (title, content, published_at) VALUES (?, ?, ?)", (title, content, published_at))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_news'))
        flash('Заполните заголовок и текст новости.', 'error')
    return render_template('admin/news_form.html', item=None)

@app.route('/admin/news/<int:item_id>/edit/', methods=['GET', 'POST'])
@login_required
def admin_news_edit(item_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM news WHERE id = ?", (item_id,)).fetchone()
    if not item:
        conn.close()
        flash('Новость не найдена.', 'error')
        return redirect(url_for('admin_news'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        published_at = request.form.get('published_at', '').strip()
        is_published = 1 if request.form.get('is_published') else 0
        conn.execute(
            "UPDATE news SET title=?, content=?, published_at=?, is_published=? WHERE id=?",
            (title, content, published_at, is_published, item_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_news'))

    conn.close()
    return render_template('admin/news_form.html', item=item)

@app.route('/admin/news/<int:item_id>/delete/', methods=['POST'])
@login_required
def admin_news_delete(item_id):
    conn = get_db()
    conn.execute("DELETE FROM news WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_news'))

@app.route('/admin/categories/')
@login_required
def admin_categories():
    conn = get_db()
    items = conn.execute("SELECT * FROM categories ORDER BY sort_order, id").fetchall()
    conn.close()
    return render_template('admin/categories.html', items=items)

@app.route('/admin/categories/add/', methods=['GET', 'POST'])
@login_required
def admin_category_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        sort_order = request.form.get('sort_order', '0').strip() or '0'
        if name:
            conn = get_db()
            conn.execute("INSERT INTO categories (name, description, sort_order) VALUES (?, ?, ?)", (name, description, sort_order))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_categories'))
        flash('Введите название категории.', 'error')
    return render_template('admin/category_form.html', item=None)

@app.route('/admin/categories/<int:item_id>/edit/', methods=['GET', 'POST'])
@login_required
def admin_category_edit(item_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM categories WHERE id = ?", (item_id,)).fetchone()
    if not item:
        conn.close()
        return redirect(url_for('admin_categories'))

    if request.method == 'POST':
        conn.execute(
            "UPDATE categories SET name=?, description=?, sort_order=?, is_active=? WHERE id=?",
            (
                request.form.get('name', '').strip(),
                request.form.get('description', '').strip(),
                request.form.get('sort_order', '0').strip() or '0',
                1 if request.form.get('is_active') else 0,
                item_id
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_categories'))

    conn.close()
    return render_template('admin/category_form.html', item=item)

@app.route('/admin/categories/<int:item_id>/delete/', methods=['POST'])
@login_required
def admin_category_delete(item_id):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_categories'))

@app.route('/admin/products/')
@login_required
def admin_products():
    conn = get_db()
    items = conn.execute("""
        SELECT products.*, categories.name AS category_name
        FROM products
        LEFT JOIN categories ON categories.id = products.category_id
        ORDER BY products.id DESC
    """).fetchall()
    conn.close()
    return render_template('admin/products.html', items=items)

@app.route('/admin/products/add/', methods=['GET', 'POST'])
@login_required
def admin_product_add():
    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY sort_order, id").fetchall()
    if request.method == 'POST':
        conn.execute(
            "INSERT INTO products (category_id, name, description, material, weight, in_stock, is_published) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                request.form.get('category_id') or None,
                request.form.get('name', '').strip(),
                request.form.get('description', '').strip(),
                request.form.get('material', '').strip(),
                request.form.get('weight', '').strip(),
                1 if request.form.get('in_stock') else 0,
                1 if request.form.get('is_published') else 0,
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))
    conn.close()
    return render_template('admin/product_form.html', item=None, categories=categories)

@app.route('/admin/products/<int:item_id>/edit/', methods=['GET', 'POST'])
@login_required
def admin_product_edit(item_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM products WHERE id = ?", (item_id,)).fetchone()
    categories = conn.execute("SELECT * FROM categories ORDER BY sort_order, id").fetchall()
    if not item:
        conn.close()
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        conn.execute(
            "UPDATE products SET category_id=?, name=?, description=?, material=?, weight=?, in_stock=?, is_published=? WHERE id=?",
            (
                request.form.get('category_id') or None,
                request.form.get('name', '').strip(),
                request.form.get('description', '').strip(),
                request.form.get('material', '').strip(),
                request.form.get('weight', '').strip(),
                1 if request.form.get('in_stock') else 0,
                1 if request.form.get('is_published') else 0,
                item_id
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))

    conn.close()
    return render_template('admin/product_form.html', item=item, categories=categories)

@app.route('/admin/products/<int:item_id>/delete/', methods=['POST'])
@login_required
def admin_product_delete(item_id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_products'))


if __name__ == '__main__':
    app.run(debug=True)
