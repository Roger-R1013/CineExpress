// ── ESTADO GLOBAL ──────────────────────────────────────────────────────────
let peliculaActual   = null;
let horarioActual    = null;
let asientosSeleccionados = [];

// ── UTILIDADES ─────────────────────────────────────────────────────────────
function scrollSec(id) {
  document.getElementById(id).scrollIntoView({ behavior: 'smooth' });
}

function showToast(msg, dur = 3500) {
  const t = document.getElementById('toast');
  t.innerHTML = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), dur);
}

// ── NAVBAR SCROLL ──────────────────────────────────────────────────────────
window.addEventListener('scroll', () => {
  document.getElementById('navbar').style.background =
    window.scrollY > 50 ? 'rgba(0,0,0,.99)' : '';
});

// ── FILTROS CARTELERA ──────────────────────────────────────────────────────
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter.toLowerCase();
    document.querySelectorAll('.movie-card').forEach(card => {
      const g = (card.dataset.genero || '').toLowerCase();
      card.classList.toggle('hidden', f !== 'todas' && !g.includes(f));
    });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// MODAL PELÍCULA  —  usa data-* para evitar problemas de comillas
// ══════════════════════════════════════════════════════════════════════════
function abrirPelicula(el) {
  const id     = el.dataset.id;
  const titulo = el.dataset.titulo;
  const genero = el.dataset.genero2;
  const desc   = el.dataset.desc;
  const cal    = el.dataset.cal;
  const img    = el.dataset.img;
  openModal(id, titulo, genero, desc, cal, img);
}

async function openModal(id, titulo, genero, desc, rating, imagen) {
  peliculaActual = { id, titulo, genero, desc, rating, imagen };
  horarioActual  = null;
  asientosSeleccionados = [];

  document.getElementById('modalTitle').textContent  = titulo;
  document.getElementById('modalGenre').textContent  = genero;
  document.getElementById('modalDesc').textContent   = desc;
  document.getElementById('modalRating').textContent = rating;
  document.getElementById('modalImg').src            = imagen;
  document.getElementById('seccionAsientos').style.display = 'none';
  document.getElementById('salaGrid').innerHTML      = '';
  document.getElementById('asientosSelText').textContent = 'Ninguno';
  actualizarTotal();

  const grid = document.getElementById('horariosGrid');
  grid.innerHTML = '<span style="color:var(--plomo-texto);font-size:.8rem">Cargando horarios...</span>';

  try {
    const res     = await fetch('/api/horarios/' + id);
    const horarios = await res.json();
    grid.innerHTML = '';
    if (horarios.length === 0) {
      grid.innerHTML = '<span style="color:var(--plomo-texto)">Sin horarios disponibles</span>';
    } else {
      horarios.forEach(h => {
        const pill = document.createElement('div');
        pill.className   = 'horario-pill';
        pill.textContent = h.hora + ' · ' + h.sala_nombre;
        pill.onclick     = () => seleccionarHorario(pill, h);
        grid.appendChild(pill);
      });
    }
  } catch(e) {
    grid.innerHTML = '<span style="color:var(--plomo-texto)">Error cargando horarios</span>';
  }

  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

async function seleccionarHorario(el, horario) {
  document.querySelectorAll('.horario-pill').forEach(p => p.classList.remove('selected'));
  el.classList.add('selected');
  horarioActual = horario;
  asientosSeleccionados = [];

  const sec = document.getElementById('seccionAsientos');
  sec.style.display = 'block';
  document.getElementById('infoSala').textContent =
    horario.sala_nombre + ' · ' + horario.filas + ' filas × ' + horario.columnas + ' columnas';

  await cargarAsientos(horario.id, horario.filas, horario.columnas);
  actualizarTotal();
}

async function cargarAsientos(horarioId, filas, columnas) {
  const grid = document.getElementById('salaGrid');
  grid.innerHTML = '<span style="color:var(--plomo-texto);font-size:.8rem">Cargando asientos...</span>';

  try {
    const res  = await fetch('/api/asientos/' + horarioId);
    const data = await res.json();
    const ocupados = new Set(data.ocupados.map(a => a.fila + '-' + a.columna));
    const letras   = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

    grid.innerHTML = '';
    for (let f = 0; f < filas; f++) {
      const fila = document.createElement('div');
      fila.className = 'sala-fila';

      const lbl = document.createElement('span');
      lbl.className   = 'fila-label';
      lbl.textContent = letras[f];
      fila.appendChild(lbl);

      for (let c = 1; c <= columnas; c++) {
        const key  = letras[f] + '-' + c;
        const btn  = document.createElement('div');
        btn.className  = 'asiento ' + (ocupados.has(key) ? 'ocupado' : 'libre');
        btn.title      = letras[f] + c;
        btn.dataset.key = key;
        if (!ocupados.has(key)) {
          btn.onclick = () => toggleAsiento(btn, key);
        }
        fila.appendChild(btn);
      }
      grid.appendChild(fila);
    }
  } catch(e) {
    grid.innerHTML = '<span style="color:var(--plomo-texto)">Error cargando asientos</span>';
  }
}

function toggleAsiento(el, key) {
  if (el.classList.contains('seleccionado')) {
    el.classList.replace('seleccionado', 'libre');
    asientosSeleccionados = asientosSeleccionados.filter(k => k !== key);
  } else {
    el.classList.replace('libre', 'seleccionado');
    asientosSeleccionados.push(key);
  }
  document.getElementById('asientosSelText').textContent =
    asientosSeleccionados.length === 0 ? 'Ninguno' : asientosSeleccionados.join(', ');
  actualizarTotal();
}

function actualizarTotal() {
  const select = document.getElementById('modalEntradaTipo');
  if (!select) return;
  const precio   = parseFloat(select.options[select.selectedIndex].dataset.precio || 0);
  const cantidad = Math.max(asientosSeleccionados.length, 1);
  document.getElementById('modalTotalPrecio').textContent = 'Bs. ' + (precio * cantidad).toFixed(0);
}

async function confirmarCompra() {
  if (!horarioActual) {
    showToast('Selecciona un horario primero'); return;
  }
  if (asientosSeleccionados.length === 0) {
    showToast('Selecciona al menos un asiento'); return;
  }
  const select   = document.getElementById('modalEntradaTipo');
  const tipo     = select.value;
  const precio   = parseFloat(select.options[select.selectedIndex].dataset.precio);
  const total    = precio * asientosSeleccionados.length;

  try {
    const res  = await fetch('/api/comprar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pelicula_id:  peliculaActual.id,
        horario_id:   horarioActual.id,
        asientos:     asientosSeleccionados,
        entrada_tipo: tipo,
        cantidad:     asientosSeleccionados.length,
        total:        total
      })
    });
    const data = await res.json();
    if (data.ok) {
      closeModalDirect();
      showToast('Compra confirmada. ' + asientosSeleccionados.length +
        ' entrada(s) para <b>' + peliculaActual.titulo + '</b>. +' + total + ' puntos');
      setTimeout(() => location.reload(), 3000);
    } else {
      showToast(data.msg);
      if (data.msg && data.msg.includes('sesión')) setTimeout(() => openLogin(), 1500);
    }
  } catch(e) {
    showToast('Error de conexión. Intenta de nuevo.');
  }
}

function cerrarModalFondo(e) {
  if (e.target.id === 'modalOverlay') closeModalDirect();
}
function closeModalDirect() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

// ══════════════════════════════════════════════════════════════════════════
// CARRITO
// ══════════════════════════════════════════════════════════════════════════
function toggleCarrito() {
  const panel   = document.getElementById('carritoPanel');
  const overlay = document.getElementById('carritoOverlay');
  const abierto = panel.classList.toggle('open');
  overlay.classList.toggle('show', abierto);
  if (abierto) renderCarrito();
}

function agregarEntradaCarrito(btn) {
  const id     = btn.dataset.id;
  const nombre = btn.dataset.nombre;
  const precio = parseFloat(btn.dataset.precio);
  agregarCarrito('entrada', id, nombre, precio);
}

function agregarMenuCarrito(el) {
  const id     = el.dataset.id;
  const nombre = el.dataset.nombre;
  const precio = parseFloat(el.dataset.precio);
  agregarCarrito('menu', id, nombre, precio);
}

async function agregarCarrito(tipo, itemId, nombre, precio) {
  try {
    const res  = await fetch('/api/carrito/agregar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tipo, item_id: itemId, nombre, precio })
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById('carritoCount').textContent = data.total_carrito;
      showToast('<b>' + nombre + '</b> agregado al carrito');
    }
  } catch(e) {
    showToast('Error al agregar al carrito');
  }
}

async function renderCarrito() {
  const container = document.getElementById('carritoItems');
  const totalEl   = document.getElementById('carritoTotal');

  try {
    const res   = await fetch('/api/carrito');
    const items = await res.json();

    if (items.length === 0) {
      container.innerHTML = '<p class="carrito-vacio">Tu carrito está vacío</p>';
      totalEl.textContent = 'Bs. 0';
      return;
    }

    let total = 0;
    container.innerHTML = '';
    items.forEach(item => {
      const subtotal = item.precio * item.cantidad;
      total += subtotal;
      const div = document.createElement('div');
      div.className = 'carrito-item';
      div.innerHTML =
        '<div class="carrito-item-info">' +
          '<div class="carrito-item-nombre">' + item.nombre + '</div>' +
          '<div class="carrito-item-precio">Bs. ' + subtotal.toFixed(0) + '</div>' +
        '</div>' +
        '<button class="carrito-item-remove" onclick="eliminarItem(' + item.id + ')">X</button>';
      container.appendChild(div);
    });
    totalEl.textContent = 'Bs. ' + total.toFixed(0);
  } catch(e) {
    container.innerHTML = '<p class="carrito-vacio">Error al cargar el carrito</p>';
  }
}

async function eliminarItem(id) {
  await fetch('/api/carrito/eliminar/' + id, { method: 'POST' });
  const res   = await fetch('/api/carrito');
  const items = await res.json();
  document.getElementById('carritoCount').textContent = items.length;
  renderCarrito();
}

async function vaciarCarrito() {
  await fetch('/api/carrito/vaciar', { method: 'POST' });
  document.getElementById('carritoCount').textContent = '0';
  renderCarrito();
  showToast('Carrito vaciado');
}

async function finalizarCompra() {
  const res   = await fetch('/api/carrito');
  const items = await res.json();
  if (items.length === 0) { showToast('Tu carrito está vacío'); return; }
  const total = items.reduce((s, i) => s + i.precio * i.cantidad, 0);
  await vaciarCarrito();
  toggleCarrito();
  showToast('Compra finalizada. Total: <b>Bs. ' + total.toFixed(0) + '</b>. Gracias por elegir CINE EXPRESS.');
}

// ══════════════════════════════════════════════════════════════════════════
// LOGIN / REGISTRO
// ══════════════════════════════════════════════════════════════════════════
function openLogin() {
  document.getElementById('loginOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeLoginDirect() {
  document.getElementById('loginOverlay').classList.remove('open');
  document.body.style.overflow = '';
}
function cerrarLoginFondo(e) {
  if (e.target.id === 'loginOverlay') closeLoginDirect();
}
function switchLoginTab(tab, el) {
  document.querySelectorAll('.login-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('login-form').style.display    = tab === 'login'    ? 'block' : 'none';
  document.getElementById('registro-form').style.display = tab === 'registro' ? 'block' : 'none';
}

async function doLogin() {
  const email    = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPass').value;
  const msg      = document.getElementById('loginMsg');
  if (!email || !password) {
    msg.textContent = 'Completa todos los campos';
    msg.className   = 'form-msg error'; return;
  }
  try {
    const res  = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.ok) {
      msg.textContent = 'Bienvenido, ' + data.nombre;
      msg.className   = 'form-msg success';
      setTimeout(() => location.reload(), 1200);
    } else {
      msg.textContent = data.msg;
      msg.className   = 'form-msg error';
    }
  } catch(e) {
    msg.textContent = 'Error de conexión';
    msg.className   = 'form-msg error';
  }
}

async function doRegistro() {
  const nombre   = document.getElementById('regNombre').value.trim();
  const email    = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPass').value;
  const msg      = document.getElementById('regMsg');

  if (!nombre || !email || !password) {
    msg.textContent = 'Completa todos los campos';
    msg.className   = 'form-msg error'; return;
  }

  // Validación: el nombre solo debe contener letras y espacios (incluye tildes y ñ)
  const soloLetras = /^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]+$/;
  if (!soloLetras.test(nombre)) {
    msg.textContent = 'El nombre solo debe contener letras, sin números ni caracteres especiales';
    msg.className   = 'form-msg error'; return;
  }

  try {
    const res  = await fetch('/registro', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, email, password })
    });
    const data = await res.json();
    if (data.ok) {
      msg.textContent = 'Cuenta creada. Bienvenido, ' + data.nombre;
      msg.className   = 'form-msg success';
      setTimeout(() => location.reload(), 1200);
    } else {
      msg.textContent = data.msg;
      msg.className   = 'form-msg error';
    }
  } catch(e) {
    msg.textContent = 'Error de conexión';
    msg.className   = 'form-msg error';
  }
}

// ══════════════════════════════════════════════════════════════════════════
// PERFIL TABS
// ══════════════════════════════════════════════════════════════════════════
function switchTab(tabId, el) {
  document.querySelectorAll('.perfil-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-' + tabId).classList.add('active');
}

async function cargarPerfil() {
  try {
    const res = await fetch('/perfil');
    if (!res.ok) return;
    const data = await res.json();

    const sc = document.getElementById('stat-compras');
    const st = document.getElementById('stat-total');
    if (sc) sc.textContent = data.compras.length;
    if (st) {
      const totalGastado = data.compras.reduce((s, c) => s + (c.total || 0), 0);
      st.textContent = totalGastado.toFixed(0);
    }

    const renderItems = (items) => {
      if (!items || items.length === 0)
        return '<p style="color:var(--plomo-texto);font-size:.85rem">Aún no tienes compras.</p>';
      return items.map(c =>
        '<div class="historial-item">' +
          '<div class="historial-dot"></div>' +
          '<div class="historial-movie">' + (c.titulo || 'Producto') +
            ' — ' + c.entrada_tipo +
            ' (' + c.cantidad + ' entrada' + (c.cantidad > 1 ? 's' : '') + ')</div>' +
          '<div class="historial-date">' + (c.fecha || '').slice(0,10) + '</div>' +
        '</div>'
      ).join('');
    };

    const hl = document.getElementById('historial-list');
    const hc = document.getElementById('historial-completo');
    if (hl) hl.innerHTML = renderItems(data.compras.slice(0, 4));
    if (hc) hc.innerHTML = renderItems(data.compras);
  } catch(e) { /* usuario no logueado */ }
}

// ══════════════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
  cargarPerfil();
  try {
    const res   = await fetch('/api/carrito');
    const items = await res.json();
    document.getElementById('carritoCount').textContent = items.length;
  } catch(e) {}
});