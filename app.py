import os
import json
import sqlite3
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Cheremsha')
DB_PATH = 'data.db'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ──────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS kv (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS zitate (
            id TEXT PRIMARY KEY,
            tag TEXT,
            tag_color TEXT,
            text TEXT,
            source TEXT,
            border_color TEXT,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS themen (
            id TEXT PRIMARY KEY,
            icon TEXT,
            icon_bg TEXT,
            title TEXT,
            body TEXT,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS interviews (
            id TEXT PRIMARY KEY,
            name TEXT,
            role TEXT,
            initials TEXT,
            avatar_color TEXT,
            accent_color TEXT,
            avatar_img TEXT,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS interview_qa (
            id TEXT PRIMARY KEY,
            interview_id TEXT,
            question TEXT,
            answer TEXT,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        );
        """)
        # Seed defaults if empty
        row = db.execute("SELECT COUNT(*) as c FROM kv").fetchone()
        if row['c'] == 0:
            defaults = {
                'rez-title': 'Der Tunnelbauer – eine Reise in die Tiefe',
                'rez-text': '<p>Marie Nelsens Roman <em>„Der Tunnelbauer"</em> ist ein eindrucksvolles Werk, das auf mehreren Ebenen funktioniert: als packende Geschichte über einen einsamen Ingenieur, als Metapher für menschliche Isolation und als philosophische Betrachtung über das Graben.</p><p>Im Mittelpunkt steht Hermann Schacht, ein alter Tunnelbauer, der sich in seiner Arbeit verliert. Nelsen schreibt mit einer Präzision, die an die Tunnelwände selbst erinnert: glatt, kalt und doch voller verborgener Risse.</p><p>Besonders beeindruckend ist, wie die Autorin die innere Welt ihrer Figur mit der physischen Arbeit verknüpft. Jeder Meter, den Hermann gräbt, ist gleichzeitig ein Schritt tiefer in seine eigene Vergangenheit.</p>',
                'stars': '4',
                'book-title': 'Der Tunnelbauer',
                'book-author': 'Marie Nelsen',
                'book-verlag': 'Hanser Verlag',
                'book-year': '2021',
                'book-pages': '312',
                'book-genre': 'Literaturoman',
                'book-cover-img': '',
                'header-subtitle': 'Buchanalyse · Charaktere & Motive · Zitate & Interviews',
            }
            for k, v in defaults.items():
                db.execute("INSERT INTO kv(key,value) VALUES(?,?)", (k, v))

        row = db.execute("SELECT COUNT(*) as c FROM zitate").fetchone()
        if row['c'] == 0:
            zitate = [
                ('z1', 'Einsamkeit', '#FF6B35', '„Man gräbt nicht, um voranzukommen. Man gräbt, weil man nicht weiß, wo oben ist."', '— Kapitel 3, S. 47', '#FF6B35', 0),
                ('z2', 'Arbeit & Identität', '#2D4A7A', '„Ein Tunnel ist nicht das Ende. Er ist das Versprechen, dass es auf der anderen Seite weitergeht."', '— Kapitel 11, S. 142', '#2D4A7A', 1),
                ('z3', 'Hoffnung', '#3D9970', '„Das Licht am Ende des Tunnels – ich habe es nie geglaubt. Aber ich habe nie aufgehört zu graben."', '— Kapitel 19, S. 278', '#3D9970', 2),
            ]
            for z in zitate:
                db.execute("INSERT INTO zitate VALUES(?,?,?,?,?,?,?)", z)

        row = db.execute("SELECT COUNT(*) as c FROM themen").fetchone()
        if row['c'] == 0:
            themen = [
                ('t1', '🕳️', 'rgba(255,107,53,0.12)', 'Der Tunnel als Metapher', 'Der Tunnel symbolisiert den inneren Rückzug des Protagonisten. Je tiefer er gräbt, desto weiter entfernt er sich von der Gesellschaft.', 0),
                ('t2', '👤', 'rgba(45,74,122,0.12)', 'Identität & Verlust', 'Hermann verliert im Laufe des Romans seine berufliche und soziale Identität. Wer ist man, wenn die Arbeit wegfällt?', 1),
                ('t3', '🌅', 'rgba(247,201,72,0.2)', 'Hoffnung & Neubeginn', 'Trotz aller Dunkelheit enthält der Roman eine zarte Hoffnung: dass jeder Tunnel irgendwo endet.', 2),
                ('t4', '🤝', 'rgba(61,153,112,0.12)', 'Menschliche Verbindung', 'Die wenigen Momente echter Verbindung im Buch stechen umso stärker hervor – ein Blick, ein Gespräch, eine Berührung.', 3),
            ]
            for t in themen:
                db.execute("INSERT INTO themen VALUES(?,?,?,?,?,?)", t)

        row = db.execute("SELECT COUNT(*) as c FROM interviews").fetchone()
        if row['c'] == 0:
            db.execute("INSERT INTO interviews VALUES(?,?,?,?,?,?,?,?)",
                ('i1','Hermann Schacht','Protagonist, Tunnelbauer, 67 Jahre alt','HS','#FF6B35','#FF6B35','',0))
            db.execute("INSERT INTO interviews VALUES(?,?,?,?,?,?,?,?)",
                ('i2','Klara Meier','Hermans Tochter, Ärztin, 38 Jahre alt','KM','#2D4A7A','#2D4A7A','',1))
            qa = [
                ('q1i1','i1','Herr Schacht, warum haben Sie Ihr Leben dem Tunnelbau gewidmet?','„Weil die Erde ehrlich ist. Sie lügt nicht. Wenn man gräbt, weiß man, was man bekommt. Menschen... Menschen lügen viel mehr."',0),
                ('q2i1','i1','Haben Sie je Angst vor der Dunkelheit gehabt?','„Die Dunkelheit ist mein Zuhause. Es ist das Licht, das mich manchmal erschreckt."',1),
                ('q1i2','i2','Wie war es, mit einem Vater aufzuwachsen, der immer „unter der Erde" war?','„Ich habe früh gelernt, alleine zu sein. Aber ich habe auch gelernt, auf ihn zu warten. Er kam immer zurück – schmutziger, aber irgendwie erleichtert."',0),
                ('q2i2','i2','Was wünschen Sie sich für ihn?','„Dass er irgendwann aufhört zu graben. Und einfach... bleibt."',1),
            ]
            for q in qa:
                db.execute("INSERT INTO interview_qa VALUES(?,?,?,?,?)", q)

init_db()

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def get_all_data():
    db = get_db()
    kv = {r['key']: r['value'] for r in db.execute("SELECT key,value FROM kv").fetchall()}

    zitate = [dict(r) for r in db.execute("SELECT * FROM zitate ORDER BY sort_order").fetchall()]
    themen = [dict(r) for r in db.execute("SELECT * FROM themen ORDER BY sort_order").fetchall()]

    interviews_raw = db.execute("SELECT * FROM interviews ORDER BY sort_order").fetchall()
    interviews = []
    for iv in interviews_raw:
        iv_dict = dict(iv)
        qa = [dict(r) for r in db.execute(
            "SELECT * FROM interview_qa WHERE interview_id=? ORDER BY sort_order", (iv['id'],)
        ).fetchall()]
        iv_dict['qa'] = qa
        interviews.append(iv_dict)

    db.close()
    return {'kv': kv, 'zitate': zitate, 'themen': themen, 'interviews': interviews}

# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    return jsonify(get_all_data())

@app.route('/api/auth', methods=['POST'])
def api_auth():
    pw = request.json.get('password','')
    if pw == ADMIN_PASSWORD:
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 401

@app.route('/api/kv', methods=['POST'])
def api_kv():
    data = request.json
    with get_db() as db:
        for k, v in data.items():
            db.execute("INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
    return jsonify({'ok': True})

# --- Zitate ---
@app.route('/api/zitat', methods=['POST'])
def api_zitat_create():
    d = request.json
    nid = d.get('id', 'z' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) as c FROM zitate").fetchone()['c']
        db.execute("INSERT INTO zitate VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET tag=excluded.tag,tag_color=excluded.tag_color,text=excluded.text,source=excluded.source,border_color=excluded.border_color,sort_order=excluded.sort_order",
            (nid, d.get('tag','Thema'), d.get('tag_color','#FF6B35'), d.get('text','Zitat...'), d.get('source','— S. XX'), d.get('border_color','#FF6B35'), d.get('sort_order', count)))
    return jsonify({'ok': True, 'id': nid})

@app.route('/api/zitat/<zid>', methods=['PUT'])
def api_zitat_update(zid):
    d = request.json
    with get_db() as db:
        db.execute("UPDATE zitate SET tag=?,tag_color=?,text=?,source=?,border_color=? WHERE id=?",
            (d.get('tag'), d.get('tag_color'), d.get('text'), d.get('source'), d.get('border_color'), zid))
    return jsonify({'ok': True})

@app.route('/api/zitat/<zid>', methods=['DELETE'])
def api_zitat_delete(zid):
    with get_db() as db:
        db.execute("DELETE FROM zitate WHERE id=?", (zid,))
    return jsonify({'ok': True})

# --- Themen ---
@app.route('/api/thema', methods=['POST'])
def api_thema_create():
    d = request.json
    nid = d.get('id', 't' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) as c FROM themen").fetchone()['c']
        db.execute("INSERT INTO themen VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET icon=excluded.icon,icon_bg=excluded.icon_bg,title=excluded.title,body=excluded.body,sort_order=excluded.sort_order",
            (nid, d.get('icon','💡'), d.get('icon_bg','rgba(255,107,53,0.12)'), d.get('title','Neues Thema'), d.get('body','Beschreibung...'), d.get('sort_order', count)))
    return jsonify({'ok': True, 'id': nid})

@app.route('/api/thema/<tid>', methods=['PUT'])
def api_thema_update(tid):
    d = request.json
    with get_db() as db:
        db.execute("UPDATE themen SET icon=?,icon_bg=?,title=?,body=? WHERE id=?",
            (d.get('icon'), d.get('icon_bg'), d.get('title'), d.get('body'), tid))
    return jsonify({'ok': True})

@app.route('/api/thema/<tid>', methods=['DELETE'])
def api_thema_delete(tid):
    with get_db() as db:
        db.execute("DELETE FROM themen WHERE id=?", (tid,))
    return jsonify({'ok': True})

# --- Interviews ---
@app.route('/api/interview', methods=['POST'])
def api_interview_create():
    d = request.json
    nid = d.get('id', 'i' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) as c FROM interviews").fetchone()['c']
        db.execute("INSERT INTO interviews VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,role=excluded.role,initials=excluded.initials,avatar_color=excluded.avatar_color,accent_color=excluded.accent_color,avatar_img=excluded.avatar_img,sort_order=excluded.sort_order",
            (nid, d.get('name','Name'), d.get('role','Rolle'), d.get('initials','??'), d.get('avatar_color','#2D4A7A'), d.get('accent_color','#2D4A7A'), d.get('avatar_img',''), d.get('sort_order', count)))
    return jsonify({'ok': True, 'id': nid})

@app.route('/api/interview/<iid>', methods=['PUT'])
def api_interview_update(iid):
    d = request.json
    with get_db() as db:
        db.execute("UPDATE interviews SET name=?,role=?,initials=?,avatar_color=?,accent_color=?,avatar_img=? WHERE id=?",
            (d.get('name'), d.get('role'), d.get('initials'), d.get('avatar_color'), d.get('accent_color'), d.get('avatar_img'), iid))
    return jsonify({'ok': True})

@app.route('/api/interview/<iid>', methods=['DELETE'])
def api_interview_delete(iid):
    with get_db() as db:
        db.execute("DELETE FROM interviews WHERE id=?", (iid,))
        db.execute("DELETE FROM interview_qa WHERE interview_id=?", (iid,))
    return jsonify({'ok': True})

# --- Q&A ---
@app.route('/api/qa', methods=['POST'])
def api_qa_create():
    d = request.json
    nid = d.get('id', 'qa' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute("SELECT COUNT(*) as c FROM interview_qa WHERE interview_id=?", (d['interview_id'],)).fetchone()['c']
        db.execute("INSERT INTO interview_qa VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET question=excluded.question,answer=excluded.answer,sort_order=excluded.sort_order",
            (nid, d['interview_id'], d.get('question','Frage?'), d.get('answer','Antwort...'), d.get('sort_order', count)))
    return jsonify({'ok': True, 'id': nid})

@app.route('/api/qa/<qid>', methods=['PUT'])
def api_qa_update(qid):
    d = request.json
    with get_db() as db:
        db.execute("UPDATE interview_qa SET question=?,answer=? WHERE id=?", (d.get('question'), d.get('answer'), qid))
    return jsonify({'ok': True})

@app.route('/api/qa/<qid>', methods=['DELETE'])
def api_qa_delete(qid):
    with get_db() as db:
        db.execute("DELETE FROM interview_qa WHERE id=?", (qid,))
    return jsonify({'ok': True})

# --- Upload ---
@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    if f.filename == '' or not allowed_file(f.filename):
        return jsonify({'error': 'Invalid file'}), 400
    ext = f.filename.rsplit('.',1)[1].lower()
    fname = uuid.uuid4().hex + '.' + ext
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    return jsonify({'ok': True, 'url': '/static/uploads/' + fname})

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
