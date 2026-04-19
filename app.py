import os
import re
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'site.db'
UPLOAD_DIR = BASE_DIR / 'static' / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ural_secret_key_2026')
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024


# ----------------------------- DB helpers -----------------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid


def slugify(text: str) -> str:
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    text = text.strip().lower()
    text = ''.join(mapping.get(ch, ch) for ch in text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'item'


def unique_slug(table: str, title: str, current_id=None) -> str:
    base = slugify(title)
    slug = base
    i = 2
    while True:
        if current_id:
            row = query_db(f'SELECT id FROM {table} WHERE slug = ? AND id != ?', (slug, current_id), one=True)
        else:
            row = query_db(f'SELECT id FROM {table} WHERE slug = ?', (slug,), one=True)
        if not row:
            return slug
        slug = f'{base}-{i}'
        i += 1


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_news_date(value):
    dt = parse_dt(value)
    if not dt:
        return ''
    months = ['ЯНВ', 'ФЕВ', 'МАР', 'АПР', 'МАЙ', 'ИЮН', 'ИЮЛ', 'АВГ', 'СЕН', 'ОКТ', 'НОЯ', 'ДЕК']
    return dt.strftime('%Y'), months[dt.month - 1], dt.strftime('%d.%m.%Y')


@app.template_filter('nl2br')
def nl2br(text):
    return (text or '').replace('\n', '<br>')


@app.context_processor
def inject_globals():
    categories = []
    recent_news = []
    try:
        categories = query_db('SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, name')
        recent_news = query_db(
            'SELECT * FROM news WHERE is_published = 1 ORDER BY COALESCE(published_at, created_at) DESC LIMIT 3'
        )
    except sqlite3.OperationalError:
        pass
    return {
        'nav_categories': categories,
        'footer_recent_news': recent_news,
        'is_admin_logged_in': bool(session.get('admin_id')),
    }


# ----------------------------- schema/seed -----------------------------
def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        '''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            sku TEXT,
            short_description TEXT,
            description TEXT,
            image TEXT,
            stock_status TEXT NOT NULL DEFAULT 'В наличии',
            is_published INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS product_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            value TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            summary TEXT,
            content TEXT NOT NULL,
            image TEXT,
            is_published INTEGER NOT NULL DEFAULT 1,
            published_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        '''
    )

    admin_exists = db.execute('SELECT id FROM admins LIMIT 1').fetchone()
    if not admin_exists:
        db.execute(
            'INSERT INTO admins (username, password_hash) VALUES (?, ?)',
            ('admin', generate_password_hash('admin12345')),
        )

    categories_exist = db.execute('SELECT id FROM categories LIMIT 1').fetchone()
    if not categories_exist:
        categories = [
            ('Съёмники', 'pullers', 'Специализированный инструмент для обслуживания и ремонта пассажирских вагонов РЖД.', 1),
            ('Муфты', 'couplings', 'Упругие муфты и комплектующие для приводных механизмов вагонного оборудования.', 2),
            ('ЖД Запчасти', 'railway', 'Сертифицированные запасные части для пассажирских вагонов Российских железных дорог.', 3),
        ]
        db.executemany(
            'INSERT INTO categories (name, slug, description, sort_order) VALUES (?, ?, ?, ?)', categories
        )

        cat_ids = {
            row['slug']: row['id']
            for row in db.execute('SELECT id, slug FROM categories').fetchall()
        }

        products = [
            (cat_ids['pullers'], 'Съёмник «СМУГ»', 'semnik-smug', None,
             'Съёмник муфты упругой гибкой. Применяется при обслуживании пассажирских вагонов.',
             'Съёмник муфты упругой гибкой. Обеспечивает безопасный и удобный демонтаж муфты.',
             'images/semnik-smug.jpg', 'В наличии', 1),
            (cat_ids['pullers'], 'Съёмник подшипников буксового узла', 'semnik-podshipnikov-buksovogo-uzla', None,
             'Предназначен для демонтажа подшипников буксового узла пассажирского вагона.',
             'Облегчает работы при техническом обслуживании и ремонте.',
             '', 'В наличии', 2),
            (cat_ids['pullers'], 'Съёмник шестерни редуктора', 'semnik-shesterni-reduktora', None,
             'Специализированный инструмент для безопасного снятия шестерни привода генератора.',
             'Используется при сервисном обслуживании пассажирских вагонов.',
             '', 'В наличии', 3),
            (cat_ids['couplings'], 'Муфта МППГ-02', 'mufta-mppg-02', None,
             'Муфта предохранительная привода генератора пассажирского вагона.',
             'Предназначена для передачи крутящего момента от редуктора к генератору с защитой оборудования от перегрузок.',
             'images/mufta-mppg02.jpg', 'В наличии', 1),
            (cat_ids['couplings'], 'Муфта втулочно-пальцевая МВП', 'mufta-vtulochno-palcevaya-mvp', None,
             'Применяется в приводных механизмах вагонного оборудования для компенсации несоосности валов.',
             'Надёжное решение для приводных механизмов вагонного оборудования.',
             'images/shaiba-tarelchataya.jpg', 'В наличии', 2),
            (cat_ids['couplings'], 'Полумуфта ведущая', 'polumufta-veduschaya', None,
             'Ведущая полумуфта для комплекта МППГ-02.',
             'Изготавливается из легированной стали с термической обработкой.',
             '', 'В наличии', 3),
            (cat_ids['railway'], 'Гайка крайняя', 'gayka-kraynyaya', '34.33.254',
             'Сертифицированная запчасть для пассажирских вагонов.',
             'Изготовлена в соответствии с технической документацией РЖД.',
             'images/gayka-srednyaya.jpg', 'В наличии', 1),
            (cat_ids['railway'], 'Гайка шпинтона', 'gayka-shpintona', '30.21.103',
             'Запасная часть для пассажирских вагонов.',
             'Вся продукция проходит обязательную сертификацию.',
             'images/gayka-tortsevaya.jpg', 'В наличии', 2),
            (cat_ids['railway'], 'Шайба стопорная', 'shayba-stopornaya', '34.33.255',
             'Сертифицированная запасная часть.',
             'Используется в узлах пассажирских вагонов.',
             'images/shaiba-tarelchataya.jpg', 'В наличии', 3),
        ]
        db.executemany(
            '''INSERT INTO products
               (category_id, name, slug, sku, short_description, description, image, stock_status, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            products,
        )

        prod_ids = {row['slug']: row['id'] for row in db.execute('SELECT id, slug FROM products').fetchall()}
        specs = [
            (prod_ids['semnik-smug'], 'Материал', 'Сталь 45', 1),
            (prod_ids['semnik-smug'], 'Масса', '2,8 кг', 2),
            (prod_ids['semnik-smug'], 'Применение', 'Пасс. вагоны РЖД', 3),
            (prod_ids['semnik-podshipnikov-buksovogo-uzla'], 'Материал', 'Сталь 40Х', 1),
            (prod_ids['semnik-podshipnikov-buksovogo-uzla'], 'Масса', '3,5 кг', 2),
            (prod_ids['semnik-podshipnikov-buksovogo-uzla'], 'Применение', 'Буксовый узел', 3),
            (prod_ids['semnik-shesterni-reduktora'], 'Материал', 'Сталь 45', 1),
            (prod_ids['semnik-shesterni-reduktora'], 'Усилие', 'до 15 кН', 2),
            (prod_ids['semnik-shesterni-reduktora'], 'Применение', 'Редуктор привода', 3),
            (prod_ids['mufta-mppg-02'], 'Максимальный момент', '1200 Н·м', 1),
            (prod_ids['mufta-mppg-02'], 'Частота вращения', 'до 3000 об/мин', 2),
            (prod_ids['mufta-mppg-02'], 'Материал корпуса', 'Сталь 40Х', 3),
            (prod_ids['mufta-mppg-02'], 'Масса', '4,2 кг', 4),
            (prod_ids['gayka-kraynyaya'], 'Материал', 'Сталь 40Х', 1),
            (prod_ids['gayka-shpintona'], 'Материал', 'Сталь 45', 1),
            (prod_ids['shayba-stopornaya'], 'Материал', 'Сталь 65Г', 1),
        ]
        db.executemany(
            'INSERT INTO product_specs (product_id, name, value, sort_order) VALUES (?, ?, ?, ?)', specs
        )

    news_exist = db.execute('SELECT id FROM news LIMIT 1').fetchone()
    if not news_exist:
        news_rows = [
            ('У нас появился обновлённый сайт', 'u-nas-poyavilsya-obnovlennyy-sayt',
             'Мы рады представить обновлённый официальный сайт ЗАО ПП «Урал».',
             'Мы рады представить обновлённый официальный сайт ЗАО ПП «Урал».\n\nНовый сайт содержит полный каталог продукции, информацию об услугах компании и технические характеристики изделий.\n\nСайт адаптирован для мобильных устройств и работает в современных браузерах.',
             '', '2026-03-10 10:00:00'),
            ('Расширение производственных мощностей', 'rasshirenie-proizvodstvennyh-moschnostey',
             'ЗАО ПП «Урал» приобрело новый высокоточный токарно-фрезерный обрабатывающий центр с ЧПУ.',
             'ЗАО ПП «Урал» приобрело новый высокоточный токарно-фрезерный обрабатывающий центр с ЧПУ.\n\nНовое оборудование позволяет значительно расширить возможности по обработке деталей сложной геометрии и повысить производительность производства.',
             '', '2025-12-15 10:00:00'),
            ('Сертификация продукции по ГОСТ', 'sertifikaciya-produkcii-po-gost',
             'Вся продукция предприятия прошла плановую сертификацию и подтвердила соответствие требованиям ГОСТ.',
             'Вся продукция предприятия прошла плановую сертификацию и подтвердила соответствие требованиям ГОСТ и технических условий.\n\nСертификаты соответствия обновлены на следующий период.',
             '', '2025-09-10 10:00:00'),
        ]
        db.executemany(
            'INSERT INTO news (title, slug, summary, content, image, published_at) VALUES (?, ?, ?, ?, ?, ?)',
            news_rows,
        )

    db.commit()
    db.close()


# ----------------------------- auth/upload helpers -----------------------------
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Сначала войдите в админ-панель.', 'error')
            return redirect(url_for('admin_login'))
        return view(*args, **kwargs)
    return wrapped


def save_uploaded_image(field_name='image'):
    file = request.files.get(field_name)
    if not file or not file.filename:
        return request.form.get('current_image', '').strip()
    filename = secure_filename(file.filename)
    stem, ext = os.path.splitext(filename)
    final_name = f"{slugify(stem)}-{int(datetime.now().timestamp())}{ext.lower()}"
    file_path = UPLOAD_DIR / final_name
    file.save(file_path)
    return f'uploads/{final_name}'


def replace_specs(product_id, raw_specs: str):
    db = get_db()
    db.execute('DELETE FROM product_specs WHERE product_id = ?', (product_id,))
    lines = [line.strip() for line in (raw_specs or '').splitlines() if line.strip()]
    for idx, line in enumerate(lines, start=1):
        if ':' in line:
            name, value = [part.strip() for part in line.split(':', 1)]
            if name and value:
                db.execute(
                    'INSERT INTO product_specs (product_id, name, value, sort_order) VALUES (?, ?, ?, ?)',
                    (product_id, name, value, idx),
                )
    db.commit()


# ----------------------------- public routes -----------------------------
@app.route('/')
def index():
    categories = query_db(
        'SELECT c.*, COUNT(p.id) AS product_count FROM categories c '
        'LEFT JOIN products p ON p.category_id = c.id AND p.is_published = 1 '
        'WHERE c.is_active = 1 GROUP BY c.id ORDER BY c.sort_order, c.name'
    )
    news_items = query_db(
        'SELECT * FROM news WHERE is_published = 1 ORDER BY COALESCE(published_at, created_at) DESC LIMIT 3'
    )
    return render_template('index.html', active='home', categories=categories, news_items=news_items, format_news_date=format_news_date)


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


@app.route('/catalog/')
def catalog_index():
    categories = query_db(
        'SELECT c.*, COUNT(p.id) AS product_count FROM categories c '
        'LEFT JOIN products p ON p.category_id = c.id AND p.is_published = 1 '
        'WHERE c.is_active = 1 GROUP BY c.id ORDER BY c.sort_order, c.name'
    )
    return render_template('catalog/index.html', active='catalog', categories=categories)


@app.route('/catalog/category/<slug>/')
def catalog_category(slug):
    category = query_db('SELECT * FROM categories WHERE slug = ? AND is_active = 1', (slug,), one=True)
    if not category:
        return redirect(url_for('catalog_index'))
    products = query_db(
        'SELECT * FROM products WHERE category_id = ? AND is_published = 1 ORDER BY sort_order, name',
        (category['id'],),
    )
    products_with_specs = []
    for product in products:
        specs = query_db('SELECT * FROM product_specs WHERE product_id = ? ORDER BY sort_order, id', (product['id'],))
        products_with_specs.append({'product': product, 'specs': specs})
    categories = query_db('SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, name')
    return render_template(
        'catalog/category.html', active='catalog', category=category, categories=categories, products=products_with_specs
    )


@app.route('/catalog/pullers/')
def catalog_pullers():
    return redirect(url_for('catalog_category', slug='pullers'))


@app.route('/catalog/couplings/')
def catalog_couplings():
    return redirect(url_for('catalog_category', slug='couplings'))


@app.route('/catalog/railway/')
def catalog_railway():
    return redirect(url_for('catalog_category', slug='railway'))


@app.route('/services/')
def services_index():
    return render_template('services/index.html', active='services')


@app.route('/services/metalworking/')
def services_metalworking():
    return render_template('services/metalworking.html', active='services')


@app.route('/info/')
def info_index():
    return render_template('info/index.html', active='info')


@app.route('/info/news/')
def info_news():
    items = query_db('SELECT * FROM news WHERE is_published = 1 ORDER BY COALESCE(published_at, created_at) DESC')
    return render_template('info/news.html', active='info', news_items=items, format_news_date=format_news_date)


@app.route('/info/news/<slug>/')
def news_detail(slug):
    item = query_db('SELECT * FROM news WHERE slug = ? AND is_published = 1', (slug,), one=True)
    if not item:
        return redirect(url_for('info_news'))
    latest_news = query_db(
        'SELECT * FROM news WHERE is_published = 1 AND id != ? ORDER BY COALESCE(published_at, created_at) DESC LIMIT 5',
        (item['id'],),
    )
    return render_template('info/news_detail.html', active='info', item=item, latest_news=latest_news, format_news_date=format_news_date)


@app.route('/info/articles/')
def info_articles():
    return render_template('info/articles.html', active='info')


@app.route('/info/faq/')
def info_faq():
    return render_template('info/faq.html', active='info')


@app.route('/info/agreement/')
def info_agreement():
    return render_template('info/agreement.html', active='info')


@app.route('/contacts/')
def contacts():
    return render_template('contacts.html', active='contacts')


@app.route('/contacts/submit', methods=['POST'])
def contacts_submit():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()
    if name and email and message:
        flash('Ваше сообщение отправлено. Мы свяжемся с вами в ближайшее время.', 'success')
    else:
        flash('Пожалуйста, заполните все обязательные поля формы.', 'error')
    return redirect(url_for('contacts'))


# ----------------------------- admin routes -----------------------------
@app.route('/admin/')
@admin_required
def admin_index():
    stats = {
        'news_count': query_db('SELECT COUNT(*) AS cnt FROM news', one=True)['cnt'],
        'category_count': query_db('SELECT COUNT(*) AS cnt FROM categories', one=True)['cnt'],
        'product_count': query_db('SELECT COUNT(*) AS cnt FROM products', one=True)['cnt'],
    }
    latest_news = query_db('SELECT * FROM news ORDER BY COALESCE(published_at, created_at) DESC LIMIT 5')
    latest_products = query_db('SELECT p.*, c.name as category_name FROM products p JOIN categories c ON c.id = p.category_id ORDER BY p.updated_at DESC LIMIT 5')
    return render_template('admin/dashboard.html', stats=stats, latest_news=latest_news, latest_products=latest_products)


@app.route('/admin/login/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = query_db('SELECT * FROM admins WHERE username = ?', (username,), one=True)
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            flash('Вы вошли в админ-панель.', 'success')
            return redirect(url_for('admin_index'))
        flash('Неверный логин или пароль.', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout/')
def admin_logout():
    session.clear()
    flash('Вы вышли из админ-панели.', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/news/')
@admin_required
def admin_news_list():
    items = query_db('SELECT * FROM news ORDER BY COALESCE(published_at, created_at) DESC')
    return render_template('admin/news_list.html', items=items)


@app.route('/admin/news/create/', methods=['GET', 'POST'])
@admin_required
def admin_news_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        published_at = request.form.get('published_at', '').strip() or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        is_published = 1 if request.form.get('is_published') else 0
        image = save_uploaded_image()
        if not title or not content:
            flash('Заполните заголовок и текст новости.', 'error')
            return render_template('admin/news_form.html', item=request.form, action='create')
        execute_db(
            '''INSERT INTO news (title, slug, summary, content, image, is_published, published_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (title, unique_slug('news', title), summary, content, image, is_published, published_at, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        )
        flash('Новость добавлена.', 'success')
        return redirect(url_for('admin_news_list'))
    return render_template('admin/news_form.html', item=None, action='create')


@app.route('/admin/news/<int:item_id>/edit/', methods=['GET', 'POST'])
@admin_required
def admin_news_edit(item_id):
    item = query_db('SELECT * FROM news WHERE id = ?', (item_id,), one=True)
    if not item:
        flash('Новость не найдена.', 'error')
        return redirect(url_for('admin_news_list'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        published_at = request.form.get('published_at', '').strip() or item['published_at']
        is_published = 1 if request.form.get('is_published') else 0
        image = save_uploaded_image()
        if not title or not content:
            flash('Заполните заголовок и текст новости.', 'error')
            return render_template('admin/news_form.html', item=item, action='edit')
        execute_db(
            '''UPDATE news SET title = ?, slug = ?, summary = ?, content = ?, image = ?,
               is_published = ?, published_at = ?, updated_at = ? WHERE id = ?''',
            (title, unique_slug('news', title, item_id), summary, content, image, is_published,
             published_at, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item_id),
        )
        flash('Новость обновлена.', 'success')
        return redirect(url_for('admin_news_list'))
    return render_template('admin/news_form.html', item=item, action='edit')


@app.route('/admin/news/<int:item_id>/delete/', methods=['POST'])
@admin_required
def admin_news_delete(item_id):
    execute_db('DELETE FROM news WHERE id = ?', (item_id,))
    flash('Новость удалена.', 'success')
    return redirect(url_for('admin_news_list'))


@app.route('/admin/categories/')
@admin_required
def admin_categories_list():
    items = query_db(
        'SELECT c.*, COUNT(p.id) AS product_count FROM categories c LEFT JOIN products p ON p.category_id = c.id GROUP BY c.id ORDER BY c.sort_order, c.name'
    )
    return render_template('admin/categories_list.html', items=items)


@app.route('/admin/categories/create/', methods=['GET', 'POST'])
@admin_required
def admin_category_create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        sort_order = int(request.form.get('sort_order') or 0)
        is_active = 1 if request.form.get('is_active') else 0
        if not name:
            flash('Укажите название категории.', 'error')
            return render_template('admin/category_form.html', item=None, action='create')
        execute_db(
            'INSERT INTO categories (name, slug, description, sort_order, is_active) VALUES (?, ?, ?, ?, ?)',
            (name, unique_slug('categories', name), description, sort_order, is_active),
        )
        flash('Категория добавлена.', 'success')
        return redirect(url_for('admin_categories_list'))
    return render_template('admin/category_form.html', item=None, action='create')


@app.route('/admin/categories/<int:item_id>/edit/', methods=['GET', 'POST'])
@admin_required
def admin_category_edit(item_id):
    item = query_db('SELECT * FROM categories WHERE id = ?', (item_id,), one=True)
    if not item:
        flash('Категория не найдена.', 'error')
        return redirect(url_for('admin_categories_list'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        sort_order = int(request.form.get('sort_order') or 0)
        is_active = 1 if request.form.get('is_active') else 0
        if not name:
            flash('Укажите название категории.', 'error')
            return render_template('admin/category_form.html', item=item, action='edit')
        execute_db(
            'UPDATE categories SET name = ?, slug = ?, description = ?, sort_order = ?, is_active = ? WHERE id = ?',
            (name, unique_slug('categories', name, item_id), description, sort_order, is_active, item_id),
        )
        flash('Категория обновлена.', 'success')
        return redirect(url_for('admin_categories_list'))
    return render_template('admin/category_form.html', item=item, action='edit')


@app.route('/admin/categories/<int:item_id>/delete/', methods=['POST'])
@admin_required
def admin_category_delete(item_id):
    products_count = query_db('SELECT COUNT(*) AS cnt FROM products WHERE category_id = ?', (item_id,), one=True)['cnt']
    if products_count:
        flash('Нельзя удалить категорию, пока в ней есть товары.', 'error')
    else:
        execute_db('DELETE FROM categories WHERE id = ?', (item_id,))
        flash('Категория удалена.', 'success')
    return redirect(url_for('admin_categories_list'))


@app.route('/admin/products/')
@admin_required
def admin_products_list():
    items = query_db(
        'SELECT p.*, c.name AS category_name FROM products p JOIN categories c ON c.id = p.category_id ORDER BY c.sort_order, p.sort_order, p.name'
    )
    return render_template('admin/products_list.html', items=items)


@app.route('/admin/products/create/', methods=['GET', 'POST'])
@admin_required
def admin_product_create():
    categories = query_db('SELECT * FROM categories ORDER BY sort_order, name')
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = int(request.form.get('category_id') or 0)
        sku = request.form.get('sku', '').strip()
        short_description = request.form.get('short_description', '').strip()
        description = request.form.get('description', '').strip()
        stock_status = request.form.get('stock_status', '').strip() or 'В наличии'
        sort_order = int(request.form.get('sort_order') or 0)
        is_published = 1 if request.form.get('is_published') else 0
        image = save_uploaded_image()
        if not name or not category_id:
            flash('Укажите название товара и категорию.', 'error')
            return render_template('admin/product_form.html', item=None, categories=categories, specs_text=request.form.get('specs_text', ''), action='create')
        product_id = execute_db(
            '''INSERT INTO products
               (category_id, name, slug, sku, short_description, description, image, stock_status, is_published, sort_order, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (category_id, name, unique_slug('products', name), sku, short_description, description, image,
             stock_status, is_published, sort_order, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        )
        replace_specs(product_id, request.form.get('specs_text', ''))
        flash('Товар добавлен.', 'success')
        return redirect(url_for('admin_products_list'))
    return render_template('admin/product_form.html', item=None, categories=categories, specs_text='', action='create')


@app.route('/admin/products/<int:item_id>/edit/', methods=['GET', 'POST'])
@admin_required
def admin_product_edit(item_id):
    item = query_db('SELECT * FROM products WHERE id = ?', (item_id,), one=True)
    if not item:
        flash('Товар не найден.', 'error')
        return redirect(url_for('admin_products_list'))
    categories = query_db('SELECT * FROM categories ORDER BY sort_order, name')
    specs_rows = query_db('SELECT * FROM product_specs WHERE product_id = ? ORDER BY sort_order, id', (item_id,))
    specs_text = '\n'.join(f"{row['name']}: {row['value']}" for row in specs_rows)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = int(request.form.get('category_id') or 0)
        sku = request.form.get('sku', '').strip()
        short_description = request.form.get('short_description', '').strip()
        description = request.form.get('description', '').strip()
        stock_status = request.form.get('stock_status', '').strip() or 'В наличии'
        sort_order = int(request.form.get('sort_order') or 0)
        is_published = 1 if request.form.get('is_published') else 0
        image = save_uploaded_image()
        if not name or not category_id:
            flash('Укажите название товара и категорию.', 'error')
            return render_template('admin/product_form.html', item=item, categories=categories, specs_text=request.form.get('specs_text', ''), action='edit')
        execute_db(
            '''UPDATE products SET category_id = ?, name = ?, slug = ?, sku = ?, short_description = ?,
               description = ?, image = ?, stock_status = ?, is_published = ?, sort_order = ?, updated_at = ?
               WHERE id = ?''',
            (category_id, name, unique_slug('products', name, item_id), sku, short_description, description, image,
             stock_status, is_published, sort_order, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item_id),
        )
        replace_specs(item_id, request.form.get('specs_text', ''))
        flash('Товар обновлён.', 'success')
        return redirect(url_for('admin_products_list'))
    return render_template('admin/product_form.html', item=item, categories=categories, specs_text=specs_text, action='edit')


@app.route('/admin/products/<int:item_id>/delete/', methods=['POST'])
@admin_required
def admin_product_delete(item_id):
    execute_db('DELETE FROM product_specs WHERE product_id = ?', (item_id,))
    execute_db('DELETE FROM products WHERE id = ?', (item_id,))
    flash('Товар удалён.', 'success')
    return redirect(url_for('admin_products_list'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
else:
    init_db()
