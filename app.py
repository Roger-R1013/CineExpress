from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'cineexpress_secret_2026'

DB_PATH = os.path.join(os.path.dirname(__file__), 'cineexpress.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            puntos INTEGER DEFAULT 0,
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS peliculas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            genero TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            calificacion REAL DEFAULT 0,
            imagen TEXT NOT NULL,
            estado TEXT DEFAULT 'cartelera',
            duracion INTEGER DEFAULT 120
        );
        CREATE TABLE IF NOT EXISTS salas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            filas INTEGER DEFAULT 8,
            columnas INTEGER DEFAULT 10
        );
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pelicula_id INTEGER NOT NULL,
            hora TEXT NOT NULL,
            sala_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (pelicula_id) REFERENCES peliculas(id),
            FOREIGN KEY (sala_id) REFERENCES salas(id)
        );
        CREATE TABLE IF NOT EXISTS asientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horario_id INTEGER NOT NULL,
            fila TEXT NOT NULL,
            columna INTEGER NOT NULL,
            estado TEXT DEFAULT 'libre',
            FOREIGN KEY (horario_id) REFERENCES horarios(id)
        );
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            precio REAL NOT NULL,
            tipo TEXT NOT NULL,
            icono TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            precio REAL NOT NULL,
            categoria TEXT NOT NULL,
            imagen TEXT NOT NULL,
            popular INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            pelicula_id INTEGER,
            horario_id INTEGER,
            asientos TEXT,
            entrada_tipo TEXT NOT NULL,
            cantidad INTEGER DEFAULT 1,
            total REAL NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (pelicula_id) REFERENCES peliculas(id)
        );
        CREATE TABLE IF NOT EXISTS carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            cantidad INTEGER DEFAULT 1,
            precio REAL NOT NULL,
            nombre TEXT NOT NULL
        );
    ''')

    # PELICULAS
    if c.execute("SELECT COUNT(*) FROM peliculas").fetchone()[0] == 0:
        peliculas = [
            ('Tormenta Oscura', 'accion',
             'Un ex agente de élite debe detener una conspiración global que amenaza a millones. Efectos visuales espectaculares.',
             8.4, 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&h=600&fit=crop', 'estreno', 128),
            ('Más Allá del Tiempo', 'ciencia',
             'Un científico descubre cómo viajar al futuro, pero algunos secretos es mejor no desvelar.',
             9.1, 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400&h=600&fit=crop', 'estreno', 145),
            ('El Último Bosque', 'drama',
             'Una familia enfrenta sus secretos más profundos cuando un extraño llega a su tranquilo pueblo.',
             8.7, 'https://images.unsplash.com/photo-1448375240586-882707db888b?w=400&h=600&fit=crop', 'cartelera', 112),
            ('Sangre Fría', 'suspenso',
             'Una detective recibe el caso más perturbador de su carrera: un asesino que deja pistas imposibles.',
             8.2, 'https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=400&h=600&fit=crop', 'cartelera', 118),
            ('Galaxia Perdida', 'animacion',
             'Un joven explorador espacial busca un planeta legendario donde los sueños se hacen realidad.',
             9.3, 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=400&h=600&fit=crop', 'estreno', 105),
            ('El Arte de la Mentira', 'drama',
             'En el mundo del arte contemporáneo, un joven descubre que el precio del éxito es muy alto.',
             8.6, 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=600&fit=crop', 'proximamente', 132),
        ]
        c.executemany(
            'INSERT INTO peliculas (titulo,genero,descripcion,calificacion,imagen,estado,duracion) VALUES (?,?,?,?,?,?,?)',
            peliculas
        )

    # SALAS
    if c.execute("SELECT COUNT(*) FROM salas").fetchone()[0] == 0:
        salas = [
            ('Sala 1 - General', 8, 10),
            ('Sala 2 - Premium', 6, 8),
            ('Sala 3 - VIP', 5, 6),
            ('Sala 4 - Dolby Atmos', 8, 12),
        ]
        c.executemany('INSERT INTO salas (nombre,filas,columnas) VALUES (?,?,?)', salas)

    # HORARIOS
    if c.execute("SELECT COUNT(*) FROM horarios").fetchone()[0] == 0:
        horas = ['14:30', '17:00', '19:30', '21:45']
        for pid in range(1, 7):
            for i, hora in enumerate(horas):
                sala_id = (i % 4) + 1
                c.execute(
                    'INSERT INTO horarios (pelicula_id,hora,sala_id,fecha) VALUES (?,?,?,?)',
                    (pid, hora, sala_id, '2026-05-27')
                )

    # ENTRADAS
    if c.execute("SELECT COUNT(*) FROM entradas").fetchone()[0] == 0:
        entradas = [
            ('Entrada General', 'Acceso a todas las salas estándar. Audio original con subtítulos.', 30.0, 'general', ''),
            ('Entrada Premium', 'Sala VIP con butacas reclinables, pantalla 4K y Dolby Atmos.', 55.0, 'premium', ''),
            ('Pack Familia (4 personas)', 'Cuatro entradas con ahorro especial. Válido fines de semana.', 100.0, 'familia', ''),
            ('Estudiante / Menor', 'Descuento con carnet vigente y menores de 12 años.', 22.0, 'estudiante', ''),
        ]
        c.executemany('INSERT INTO entradas (nombre,descripcion,precio,tipo,icono) VALUES (?,?,?,?,?)', entradas)

    # MENU
    if c.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] == 0:
        menu = [
            ('Pipocas Dulces', 'Palomitas bañadas en caramelo artesanal, perfectamente crujientes.', 18.0, 'snacks',
             'https://images.pexels.com/photos/30910197/pexels-photo-30910197.jpeg?auto=compress&cs=tinysrgb&w=400&h=300&fit=crop', 1),
            ('Pipocas Saladas', 'Palomitas clásicas con mantequilla y sal marina.', 15.0, 'snacks',
             'https://images.pexels.com/photos/33129/popcorn-movie-party-entertainment.jpg?auto=compress&cs=tinysrgb&w=400&h=300&fit=crop', 0),
            ('Coca-Cola', 'Coca-Cola fría en vaso grande con hielo. Clásico irresistible.', 12.0, 'bebidas',
             'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&h=300&fit=crop', 1),
            ('Sprite', 'Refresco limón-lima bien frío y muy burbujeante.', 12.0, 'bebidas',
             'https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=400&h=300&fit=crop', 0),
            ('Fanta', 'Sabor naranja intenso, fresquísima con mucho gas.', 12.0, 'bebidas',
             '/static/images/Fanta1.jpg', 0),
            ('Pepsi', 'El sabor inconfundible de Pepsi en vaso grande con hielo.', 12.0, 'bebidas',
             'https://images.unsplash.com/photo-1553456558-aff63285bdd1?w=400&h=300&fit=crop', 0),
            ('Nachos', 'Nachos crujientes con queso cheddar fundido y jalapeños.', 22.0, 'snacks',
             'https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=400&h=300&fit=crop', 1),
            ('Hot Dog', 'Salchicha premium en pan brioche con mostaza y kétchup.', 20.0, 'comidas',
             'https://images.pexels.com/photos/9304021/pexels-photo-9304021.jpeg?auto=compress&cs=tinysrgb&w=400&h=300&fit=crop', 0),
            ('Chocolate', 'Barra de chocolate belga premium. El dulce final perfecto.', 14.0, 'snacks',
             'https://images.unsplash.com/photo-1481391319762-47dff72954d9?w=400&h=300&fit=crop', 0),
        ]
        c.executemany(
            'INSERT INTO menu_items (nombre,descripcion,precio,categoria,imagen,popular) VALUES (?,?,?,?,?,?)',
            menu
        )

    # USUARIO demo
    if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios (nombre,email,password,puntos) VALUES (?,?,?,?)",
                  ('Iara Soliz', 'iara@cineexpress.bo', '1234', 1840))

    conn.commit()
    conn.close()

# ── RUTAS ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    peliculas = db.execute('SELECT * FROM peliculas').fetchall()
    entradas  = db.execute('SELECT * FROM entradas').fetchall()
    menu      = db.execute('SELECT * FROM menu_items').fetchall()
    usuario   = None
    if 'usuario_id' in session:
        usuario = db.execute('SELECT * FROM usuarios WHERE id=?', (session['usuario_id'],)).fetchone()
    db.close()
    return render_template('index.html', peliculas=peliculas, entradas=entradas, menu=menu, usuario=usuario)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    db = get_db()
    user = db.execute('SELECT * FROM usuarios WHERE email=? AND password=?',
                      (data['email'], data['password'])).fetchone()
    db.close()
    if user:
        session['usuario_id'] = user['id']
        return jsonify({'ok': True, 'nombre': user['nombre']})
    return jsonify({'ok': False, 'msg': 'Email o contraseña incorrectos'})

@app.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    nombre = data.get('nombre', '').strip()

    # Validación backend: solo letras, tildes, ñ y espacios
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]+$', nombre):
        return jsonify({'ok': False, 'msg': 'El nombre solo debe contener letras, sin números ni caracteres especiales'})

    db = get_db()
    try:
        db.execute('INSERT INTO usuarios (nombre,email,password) VALUES (?,?,?)',
                   (nombre, data['email'], data['password']))
        db.commit()
        user = db.execute('SELECT * FROM usuarios WHERE email=?', (data['email'],)).fetchone()
        session['usuario_id'] = user['id']
        db.close()
        return jsonify({'ok': True, 'nombre': nombre})
    except Exception as e:
        db.close()
        return jsonify({'ok': False, 'msg': 'El email ya está registrado'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        return jsonify({'error': 'no auth'}), 401
    db = get_db()
    usuario = db.execute('SELECT * FROM usuarios WHERE id=?', (session['usuario_id'],)).fetchone()
    compras = db.execute('''
        SELECT c.*, p.titulo FROM compras c
        LEFT JOIN peliculas p ON c.pelicula_id = p.id
        WHERE c.usuario_id = ? ORDER BY c.fecha DESC LIMIT 20
    ''', (session['usuario_id'],)).fetchall()
    db.close()
    return jsonify({
        'nombre': usuario['nombre'],
        'email': usuario['email'],
        'puntos': usuario['puntos'],
        'compras': [dict(r) for r in compras]
    })

@app.route('/api/horarios/<int:pelicula_id>')
def horarios(pelicula_id):
    db = get_db()
    rows = db.execute('''
        SELECT h.*, s.nombre as sala_nombre, s.filas, s.columnas
        FROM horarios h JOIN salas s ON h.sala_id = s.id
        WHERE h.pelicula_id = ?
    ''', (pelicula_id,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/asientos/<int:horario_id>')
def asientos(horario_id):
    db = get_db()
    horario = db.execute('''
        SELECT h.*, s.filas, s.columnas, s.nombre as sala_nombre
        FROM horarios h JOIN salas s ON h.sala_id = s.id
        WHERE h.id = ?
    ''', (horario_id,)).fetchone()
    if not horario:
        return jsonify({'error': 'Horario no encontrado'}), 404
    ocupados = db.execute(
        'SELECT fila, columna FROM asientos WHERE horario_id=? AND estado="ocupado"',
        (horario_id,)
    ).fetchall()
    db.close()
    ocupados_set = [{'fila': r['fila'], 'columna': r['columna']} for r in ocupados]
    return jsonify({
        'horario_id': horario_id,
        'sala': horario['sala_nombre'],
        'filas': horario['filas'],
        'columnas': horario['columnas'],
        'ocupados': ocupados_set
    })

@app.route('/api/comprar', methods=['POST'])
def comprar():
    data = request.get_json()
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'ok': False, 'msg': 'Debes iniciar sesión para comprar'})
    db = get_db()
    asientos_str = ','.join(data.get('asientos', []))
    db.execute('''
        INSERT INTO compras (usuario_id,pelicula_id,horario_id,asientos,entrada_tipo,cantidad,total)
        VALUES (?,?,?,?,?,?,?)
    ''', (usuario_id, data['pelicula_id'], data['horario_id'],
          asientos_str, data['entrada_tipo'], data.get('cantidad', 1), data['total']))
    for asiento in data.get('asientos', []):
        partes = asiento.split('-')
        if len(partes) == 2:
            db.execute(
                'INSERT OR REPLACE INTO asientos (horario_id,fila,columna,estado) VALUES (?,?,?,?)',
                (data['horario_id'], partes[0], partes[1], 'ocupado')
            )
    db.execute('UPDATE usuarios SET puntos = puntos + ? WHERE id=?',
               (int(data['total']), usuario_id))
    db.commit()
    db.close()
    return jsonify({'ok': True, 'msg': 'Compra realizada con exito'})

@app.route('/api/carrito', methods=['GET'])
def get_carrito():
    usuario_id = session.get('usuario_id', 1)
    db = get_db()
    items = db.execute('SELECT * FROM carrito WHERE usuario_id=?', (usuario_id,)).fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/carrito/agregar', methods=['POST'])
def agregar_carrito():
    data = request.get_json()
    usuario_id = session.get('usuario_id', 1)
    db = get_db()
    db.execute('INSERT INTO carrito (usuario_id,tipo,item_id,cantidad,precio,nombre) VALUES (?,?,?,?,?,?)',
               (usuario_id, data['tipo'], data['item_id'], 1, data['precio'], data['nombre']))
    db.commit()
    total = db.execute('SELECT COUNT(*) FROM carrito WHERE usuario_id=?', (usuario_id,)).fetchone()[0]
    db.close()
    return jsonify({'ok': True, 'total_carrito': total})

@app.route('/api/carrito/vaciar', methods=['POST'])
def vaciar_carrito():
    usuario_id = session.get('usuario_id', 1)
    db = get_db()
    db.execute('DELETE FROM carrito WHERE usuario_id=?', (usuario_id,))
    db.commit()
    db.close()
    return jsonify({'ok': True})

@app.route('/api/carrito/eliminar/<int:item_id>', methods=['POST'])
def eliminar_carrito(item_id):
    db = get_db()
    db.execute('DELETE FROM carrito WHERE id=?', (item_id,))
    db.commit()
    db.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    init_db()

    print("========================================")
    print("CINEEXPRESS - SERVIDOR INICIADO")
    print("========================================")
    print("URL: http://localhost:5001")
    print("========================================")

    app.run(host="localhost", port=5001, debug=True)