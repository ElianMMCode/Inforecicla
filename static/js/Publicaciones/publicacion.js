

// Año footer
document.getElementById('year').textContent = new Date().getFullYear();

// ====== Compartir (links rápidos) ======
const url = encodeURIComponent(globalThis.location.href);
const title = encodeURIComponent(document.getElementById('postTitle').textContent);
document.getElementById('shareWhats').href = `https://wa.me/?text=${title}%20${url}`;
document.getElementById('shareX').href = `https://twitter.com/intent/tweet?text=${title}&url=${url}`;
document.getElementById('shareFB').href = `https://www.facebook.com/sharer/sharer.php?u=${url}`;

// ====== Like / Dislike (front simulado con sessionStorage) ======
const likeBtn = document.getElementById('btnLike');
const dislikeBtn = document.getElementById('btnDislike');
const likeCount = document.getElementById('likeCount');
const dislikeCount = document.getElementById('dislikeCount');

// Claves de sesión por publicación (usa el id real en producción)
const POST_ID = new URLSearchParams(location.search).get('id') || 'post-001';
const SS_KEY = `vote:${POST_ID}`; // 'like' | 'dislike' | null

// Estado inicial
const prev = sessionStorage.getItem(SS_KEY);

function setActive(btn, active) {
    btn.classList.toggle('btn-success', active && btn === likeBtn);
    btn.classList.toggle('btn-outline-success', !(active && btn === likeBtn));
    btn.classList.toggle('btn-secondary', active && btn === dislikeBtn);
    btn.classList.toggle('btn-outline-secondary', !(active && btn === dislikeBtn));
}
setActive(likeBtn, prev === 'like');
setActive(dislikeBtn, prev === 'dislike');

likeBtn.addEventListener('click', () => {
    let likes = Number.parseInt(likeCount.textContent, 10);
    let dislikes = Number.parseInt(dislikeCount.textContent, 10);
    const current = sessionStorage.getItem(SS_KEY);

    if (current === 'like') { // quitar like
        likes = Math.max(0, likes - 1);
        sessionStorage.removeItem(SS_KEY);
        setActive(likeBtn, false);
        setActive(dislikeBtn, false);
    } else if (current === 'dislike') { // pasar de dislike a like
        dislikes = Math.max(0, dislikes - 1);
        likes += 1;
        sessionStorage.setItem(SS_KEY, 'like');
        setActive(likeBtn, true);
        setActive(dislikeBtn, false);
    } else { // sin voto -> like
        likes += 1;
        sessionStorage.setItem(SS_KEY, 'like');
        setActive(likeBtn, true);
        setActive(dislikeBtn, false);
    }
    likeCount.textContent = likes;
    dislikeCount.textContent = dislikes;

    fetch(`/publicaciones/${POST_ID}/votar/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value },
        body: 'value=1',
    }).catch(function() {});
});

dislikeBtn.addEventListener('click', () => {
    let likes = Number.parseInt(likeCount.textContent, 10);
    let dislikes = Number.parseInt(dislikeCount.textContent, 10);
    const current = sessionStorage.getItem(SS_KEY);

    if (current === 'dislike') { // quitar dislike
        dislikes = Math.max(0, dislikes - 1);
        sessionStorage.removeItem(SS_KEY);
        setActive(likeBtn, false);
        setActive(dislikeBtn, false);
    } else if (current === 'like') { // pasar de like a dislike
        likes = Math.max(0, likes - 1);
        dislikes += 1;
        sessionStorage.setItem(SS_KEY, 'dislike');
        setActive(likeBtn, false);
        setActive(dislikeBtn, true);
    } else { // sin voto -> dislike
        dislikes += 1;
        sessionStorage.setItem(SS_KEY, 'dislike');
        setActive(likeBtn, false);
        setActive(dislikeBtn, true);
    }
    likeCount.textContent = likes;
    dislikeCount.textContent = dislikes;

    fetch(`/publicaciones/${POST_ID}/votar/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value },
        body: 'value=-1',
    }).catch(function() {});
});

// ====== Comentarios (agregar en front; reemplazar por POST a tu API) ======
const commentForm = document.getElementById('commentForm');
const commentText = document.getElementById('commentText');
const commentList = document.getElementById('commentList');
const commentCount = document.getElementById('commentCount');

commentForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = commentText.value.trim();
    if (!text) return;

    // UI inmediata (optimistic)
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
    <div class="card-body">
        <div class="d-flex justify-content-between">
            <strong>Tú</strong>
            <small class="text-muted">Ahora</small>
        </div>
        <p class="mb-0"></p>
    </div>`;
    card.querySelector('p').textContent = text;
    commentList.prepend(card);
    commentText.value = '';
    commentCount.textContent = Number.parseInt(commentCount.textContent, 10) + 1;

    fetch(`/api/posts/${POST_ID}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
    }).catch(() => {
        card.remove();
        commentCount.textContent = Number.parseInt(commentCount.textContent, 10) - 1;
    });
});

// ====== (Opcional) Cargar contenido desde la BD al abrir ======
function _validarPostId(id) {
    return /^[a-zA-Z0-9_-]+$/.test(id);
}

async function cargarContenidoDesdeBD() {
    if (!POST_ID || !_validarPostId(POST_ID)) return;
    try {
        const resp = await fetch(`/api/posts/${encodeURIComponent(POST_ID)}`);
        if (!resp.ok) return;
        const data = await resp.json();
        if (typeof renderPostContent === 'function') {
            renderPostContent(data);
        }
    } catch (err) {
        console.error('Error al cargar contenido desde BD:', err);
    }
}
// Llamar desde un <script type="module"> o mediante cargarContenidoDesdeBD().catch(console.error)

