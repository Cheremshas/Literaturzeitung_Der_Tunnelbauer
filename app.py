import os
import json
import sqlite3
import uuid
from flask import (
    Flask, request, jsonify,
    send_from_directory, render_template
)
from werkzeug.utils import secure_filename


# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

app = Flask(__name__)

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATA_DIR       = os.environ.get(
    'DATA_DIR',
    os.path.join(BASE_DIR, 'data') if os.name == 'nt' else '/app/data'
)
UPLOAD_FOLDER  = os.environ.get('UPLOAD_FOLDER', os.path.join(DATA_DIR, 'uploads'))
DB_PATH        = os.environ.get('DB_PATH', os.path.join(DATA_DIR, 'data.db'))
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'tunnelbauer2025')
MAX_FILE_MB    = 16
ALLOWED_EXT    = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_MB * 1024 * 1024

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS kv (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS zitate (
                id           TEXT PRIMARY KEY,
                tag          TEXT,
                tag_color    TEXT,
                text         TEXT,
                source       TEXT,
                border_color TEXT,
                sort_order   INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS themen (
                id         TEXT PRIMARY KEY,
                icon       TEXT,
                icon_bg    TEXT,
                title      TEXT,
                body       TEXT,
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS interviews (
                id           TEXT PRIMARY KEY,
                name         TEXT,
                role         TEXT,
                initials     TEXT,
                avatar_color TEXT,
                accent_color TEXT,
                avatar_img   TEXT,
                sort_order   INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS interview_qa (
                id           TEXT PRIMARY KEY,
                interview_id TEXT,
                question     TEXT,
                answer       TEXT,
                sort_order   INTEGER DEFAULT 0,
                FOREIGN KEY(interview_id) REFERENCES interviews(id)
            );

            CREATE TABLE IF NOT EXISTS comments (
                id         TEXT PRIMARY KEY,
                author     TEXT,
                body       TEXT,
                rating     INTEGER DEFAULT 5,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        _seed_defaults(db)


def _seed_defaults(db):
    """Insert default content if the database is empty."""

    if db.execute("SELECT COUNT(*) FROM kv").fetchone()[0] == 0:
        defaults = {
            'rez-title':      'Der Tunnelbauer – eine Reise in die Tiefe',
            'rez-text':       (
                '<p>Maja Nielsens Roman <em>„Der Tunnelbauer"</em> ist ein '
                'eindrucksvolles Werk, das auf mehreren Ebenen funktioniert: '
                'als packende Geschichte über einen einsamen Jungen, als '
                'Metapher für menschliche Isolation und als philosophische '
                'Betrachtung über das Graben – im wörtlichen wie im '
                'übertragenen Sinne.</p>'
                '<p>Im Mittelpunkt steht ein Junge, der sich buchstäblich '
                'aus seiner Situation herausgräbt. Nielsen schreibt mit '
                'einer Präzision, die an die Tunnelwände selbst erinnert: '
                'rau, dunkel und doch voller verborgener Risse und Licht.</p>'
                '<p>Besonders beeindruckend ist, wie die Autorin die innere '
                'Welt ihrer Figur mit der körperlichen Arbeit verknüpft. '
                'Jeder Meter, den er gräbt, ist ein Schritt tiefer in seine '
                'eigene Geschichte.</p>'
            ),
            'stars':          '4',
            'book-title':     'Der Tunnelbauer',
            'book-author':    'Maja Nielsen',
            'book-verlag':    'Gerstenberg Verlag',
            'book-year':      '2022',
            'book-pages':     '224',
            'book-genre':     'Jugendroman',
            'book-cover-img': '/static/book_cover.png',
            'header-sub':     'Buchanalyse · Charaktere & Motive · Zitate & Interviews',
        }
        for k, v in defaults.items():
            db.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?)",
                (k, v)
            )

    if db.execute("SELECT COUNT(*) FROM zitate").fetchone()[0] == 0:
        zitate = [
            (
                'z1', 'Einsamkeit', '#E8A020',
                '„Man gräbt nicht, um voranzukommen. '
                'Man gräbt, weil man nicht weiß, wo oben ist."',
                '— Kapitel 3, S. 47', '#E8A020', 0
            ),
            (
                'z2', 'Mut', '#C0C0C0',
                '„Ein Tunnel ist nicht das Ende. Er ist das Versprechen, '
                'dass es auf der anderen Seite weitergeht."',
                '— Kapitel 11, S. 142', '#C0C0C0', 1
            ),
            (
                'z3', 'Hoffnung', '#E8A020',
                '„Das Licht am Ende des Tunnels – ich habe es nie geglaubt. '
                'Aber ich habe nie aufgehört zu graben."',
                '— Kapitel 19, S. 278', '#E8A020', 2
            ),
        ]
        for z in zitate:
            db.execute("INSERT INTO zitate VALUES(?,?,?,?,?,?,?)", z)

    if db.execute("SELECT COUNT(*) FROM themen").fetchone()[0] == 0:
        themen = [
            ('t1', '🕳️', '#E8A020', 'Der Tunnel als Metapher',
             'Der Tunnel symbolisiert den inneren Rückzug des Protagonisten. '
             'Je tiefer er gräbt, desto weiter entfernt er sich von der Welt.', 0),
            ('t2', '👦', '#C0C0C0', 'Kindheit & Stärke',
             'Der Junge wächst durch seine Aufgabe. Körperliche Arbeit wird '
             'zur inneren Reifung.', 1),
            ('t3', '🌟', '#E8A020', 'Hoffnung & Neubeginn',
             'Trotz aller Dunkelheit trägt der Roman eine zarte Hoffnung: '
             'dass jeder Tunnel irgendwo endet.', 2),
            ('t4', '🤝', '#888888', 'Vertrauen & Verrat',
             'Die wenigen Momente echter Verbindung stechen besonders hervor. '
             'Wem kann man im Dunkeln vertrauen?', 3),
        ]
        for t in themen:
            db.execute("INSERT INTO themen VALUES(?,?,?,?,?,?)", t)

    if db.execute("SELECT COUNT(*) FROM interviews").fetchone()[0] == 0:
        db.execute(
            "INSERT INTO interviews VALUES(?,?,?,?,?,?,?,?)",
            ('i1', 'Der Junge', 'Protagonist, ca. 12 Jahre alt',
             'DJ', '#E8A020', '#E8A020', '', 0)
        )
        db.execute(
            "INSERT INTO interviews VALUES(?,?,?,?,?,?,?,?)",
            ('i2', 'Der Wärter', 'Antagonist, Aufseher im Lager',
             'DW', '#888888', '#888888', '', 1)
        )
        qa_rows = [
            ('q1i1', 'i1',
             'Warum hast du angefangen zu graben?',
             '„Weil die Erde ehrlich ist. '
             'Sie lügt nicht. Wenn man gräbt, weiß man, was man bekommt."', 0),
            ('q2i1', 'i1',
             'Hattest du je Angst, dass der Tunnel einstürzt?',
             '„Jeden Tag. Aber Angst ist kein Grund aufzuhören."', 1),
            ('q1i2', 'i2',
             'Haben Sie bemerkt, dass er gräbt?',
             '„Irgendwann bemerkt man alles. '
             'Die Frage ist, wann man handelt."', 0),
        ]
        for q in qa_rows:
            db.execute("INSERT INTO interview_qa VALUES(?,?,?,?,?)", q)


init_db()


# ─────────────────────────────────────────────
#  UTILITY
# ─────────────────────────────────────────────

def allowed_file(filename):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT
    )


def get_all_data():
    db = get_db()

    kv = {
        r['key']: r['value']
        for r in db.execute("SELECT key, value FROM kv").fetchall()
    }

    zitate = [
        dict(r)
        for r in db.execute(
            "SELECT * FROM zitate ORDER BY sort_order"
        ).fetchall()
    ]

    themen = [
        dict(r)
        for r in db.execute(
            "SELECT * FROM themen ORDER BY sort_order"
        ).fetchall()
    ]

    interviews = []
    for iv in db.execute(
        "SELECT * FROM interviews ORDER BY sort_order"
    ).fetchall():
        iv_dict = dict(iv)
        iv_dict['qa'] = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM interview_qa "
                "WHERE interview_id = ? ORDER BY sort_order",
                (iv['id'],)
            ).fetchall()
        ]
        interviews.append(iv_dict)

    comments = [
        dict(r)
        for r in db.execute(
            "SELECT * FROM comments ORDER BY created_at DESC"
        ).fetchall()
    ]

    # Compute average rating
    row = db.execute(
        "SELECT AVG(rating) as avg, COUNT(*) as cnt FROM comments"
    ).fetchone()
    avg_rating = round(row['avg'], 1) if row['avg'] else 0
    comment_count = row['cnt']

    db.close()

    return {
        'kv':            kv,
        'zitate':        zitate,
        'themen':        themen,
        'interviews':    interviews,
        'comments':      comments,
        'avg_rating':    avg_rating,
        'comment_count': comment_count,
    }


# ─────────────────────────────────────────────
#  ROUTES – Pages
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─────────────────────────────────────────────
#  ROUTES – API
# ─────────────────────────────────────────────

@app.route('/api/data')
def api_data():
    return jsonify(get_all_data())


@app.route('/api/auth', methods=['POST'])
def api_auth():
    pw = request.json.get('password', '')
    if pw == ADMIN_PASSWORD:
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 401


@app.route('/api/kv', methods=['POST'])
def api_kv():
    with get_db() as db:
        for k, v in request.json.items():
            db.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (k, v)
            )
    return jsonify({'ok': True})


# ── Zitate ──────────────────────────────────

@app.route('/api/zitat', methods=['POST'])
def api_zitat_create():
    d   = request.json
    nid = d.get('id', 'z' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM zitate"
        ).fetchone()[0]
        db.execute(
            "INSERT INTO zitate VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "tag=excluded.tag, tag_color=excluded.tag_color, "
            "text=excluded.text, source=excluded.source, "
            "border_color=excluded.border_color, "
            "sort_order=excluded.sort_order",
            (
                nid,
                d.get('tag', 'Thema'),
                d.get('tag_color', '#E8A020'),
                d.get('text', 'Zitat...'),
                d.get('source', '— S. XX'),
                d.get('border_color', '#E8A020'),
                d.get('sort_order', count),
            )
        )
    return jsonify({'ok': True, 'id': nid})


@app.route('/api/zitat/<zid>', methods=['PUT'])
def api_zitat_update(zid):
    d = request.json
    with get_db() as db:
        db.execute(
            "UPDATE zitate SET "
            "tag=?, tag_color=?, text=?, source=?, border_color=? "
            "WHERE id=?",
            (
                d.get('tag'), d.get('tag_color'),
                d.get('text'), d.get('source'),
                d.get('border_color'), zid,
            )
        )
    return jsonify({'ok': True})


@app.route('/api/zitat/<zid>', methods=['DELETE'])
def api_zitat_delete(zid):
    with get_db() as db:
        db.execute("DELETE FROM zitate WHERE id=?", (zid,))
    return jsonify({'ok': True})


# ── Themen ──────────────────────────────────

@app.route('/api/thema', methods=['POST'])
def api_thema_create():
    d   = request.json
    nid = d.get('id', 't' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM themen"
        ).fetchone()[0]
        db.execute(
            "INSERT INTO themen VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "icon=excluded.icon, icon_bg=excluded.icon_bg, "
            "title=excluded.title, body=excluded.body, "
            "sort_order=excluded.sort_order",
            (
                nid,
                d.get('icon', '💡'),
                d.get('icon_bg', '#E8A020'),
                d.get('title', 'Neues Thema'),
                d.get('body', 'Beschreibung...'),
                d.get('sort_order', count),
            )
        )
    return jsonify({'ok': True, 'id': nid})


@app.route('/api/thema/<tid>', methods=['PUT'])
def api_thema_update(tid):
    d = request.json
    with get_db() as db:
        db.execute(
            "UPDATE themen SET icon=?, icon_bg=?, title=?, body=? WHERE id=?",
            (d.get('icon'), d.get('icon_bg'), d.get('title'), d.get('body'), tid)
        )
    return jsonify({'ok': True})


@app.route('/api/thema/<tid>', methods=['DELETE'])
def api_thema_delete(tid):
    with get_db() as db:
        db.execute("DELETE FROM themen WHERE id=?", (tid,))
    return jsonify({'ok': True})


# ── Interviews ──────────────────────────────

@app.route('/api/interview', methods=['POST'])
def api_interview_create():
    d   = request.json
    nid = d.get('id', 'i' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM interviews"
        ).fetchone()[0]
        db.execute(
            "INSERT INTO interviews VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "name=excluded.name, role=excluded.role, "
            "initials=excluded.initials, "
            "avatar_color=excluded.avatar_color, "
            "accent_color=excluded.accent_color, "
            "avatar_img=excluded.avatar_img, "
            "sort_order=excluded.sort_order",
            (
                nid,
                d.get('name', 'Name'),
                d.get('role', 'Rolle'),
                d.get('initials', '??'),
                d.get('avatar_color', '#E8A020'),
                d.get('accent_color', '#E8A020'),
                d.get('avatar_img', ''),
                d.get('sort_order', count),
            )
        )
    return jsonify({'ok': True, 'id': nid})


@app.route('/api/interview/<iid>', methods=['PUT'])
def api_interview_update(iid):
    d = request.json
    with get_db() as db:
        db.execute(
            "UPDATE interviews SET "
            "name=?, role=?, initials=?, "
            "avatar_color=?, accent_color=?, avatar_img=? "
            "WHERE id=?",
            (
                d.get('name'), d.get('role'), d.get('initials'),
                d.get('avatar_color'), d.get('accent_color'),
                d.get('avatar_img'), iid,
            )
        )
    return jsonify({'ok': True})


@app.route('/api/interview/<iid>', methods=['DELETE'])
def api_interview_delete(iid):
    with get_db() as db:
        db.execute("DELETE FROM interviews WHERE id=?", (iid,))
        db.execute(
            "DELETE FROM interview_qa WHERE interview_id=?", (iid,)
        )
    return jsonify({'ok': True})


# ── Q&A ─────────────────────────────────────

@app.route('/api/qa', methods=['POST'])
def api_qa_create():
    d   = request.json
    nid = d.get('id', 'qa' + uuid.uuid4().hex[:8])
    with get_db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM interview_qa WHERE interview_id=?",
            (d['interview_id'],)
        ).fetchone()[0]
        db.execute(
            "INSERT INTO interview_qa VALUES(?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "question=excluded.question, answer=excluded.answer, "
            "sort_order=excluded.sort_order",
            (
                nid,
                d['interview_id'],
                d.get('question', 'Frage?'),
                d.get('answer', 'Antwort...'),
                d.get('sort_order', count),
            )
        )
    return jsonify({'ok': True, 'id': nid})


@app.route('/api/qa/<qid>', methods=['PUT'])
def api_qa_update(qid):
    d = request.json
    with get_db() as db:
        db.execute(
            "UPDATE interview_qa SET question=?, answer=? WHERE id=?",
            (d.get('question'), d.get('answer'), qid)
        )
    return jsonify({'ok': True})


@app.route('/api/qa/<qid>', methods=['DELETE'])
def api_qa_delete(qid):
    with get_db() as db:
        db.execute("DELETE FROM interview_qa WHERE id=?", (qid,))
    return jsonify({'ok': True})


# ── Comments ────────────────────────────────

@app.route('/api/comments', methods=['GET'])
def api_comments_get():
    db = get_db()
    comments = [
        dict(r)
        for r in db.execute(
            "SELECT * FROM comments ORDER BY created_at DESC"
        ).fetchall()
    ]
    row = db.execute(
        "SELECT AVG(rating) as avg, COUNT(*) as cnt FROM comments"
    ).fetchone()
    db.close()
    return jsonify({
        'comments':      comments,
        'avg_rating':    round(row['avg'], 1) if row['avg'] else 0,
        'comment_count': row['cnt'],
    })


@app.route('/api/comments', methods=['POST'])
def api_comments_post():
    d      = request.json
    author = (d.get('author') or 'Anonym').strip()[:80]
    body   = (d.get('body') or '').strip()[:1000]
    rating = max(1, min(5, int(d.get('rating', 5))))

    if not body:
        return jsonify({'error': 'Kein Text'}), 400

    nid = 'c' + uuid.uuid4().hex[:10]
    with get_db() as db:
        db.execute(
            "INSERT INTO comments(id, author, body, rating) VALUES(?,?,?,?)",
            (nid, author, body, rating)
        )
    return jsonify({'ok': True, 'id': nid})


@app.route('/api/comments/<cid>', methods=['DELETE'])
def api_comments_delete(cid):
    with get_db() as db:
        db.execute("DELETE FROM comments WHERE id=?", (cid,))
    return jsonify({'ok': True})


# ── Upload ──────────────────────────────────

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Keine Datei'}), 400

    f = request.files['file']

    if not f.filename or not allowed_file(f.filename):
        return jsonify({'error': 'Ungültiger Dateityp'}), 400

    ext   = f.filename.rsplit('.', 1)[1].lower()
    fname = uuid.uuid4().hex + '.' + ext
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))

    return jsonify({'ok': True, 'url': '/static/uploads/' + fname})


# ─────────────────────────────────────────────
#  START
# ─────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
