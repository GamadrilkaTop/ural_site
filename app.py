from flask import Flask, render_template, request, redirect, url_for, flash

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

if __name__ == '__main__':
    app.run(debug=True)
