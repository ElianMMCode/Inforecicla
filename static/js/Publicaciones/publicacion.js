

// Año footer
document.getElementById('year').textContent = new Date().getFullYear();

// ====== Compartir (links rápidos) ======
const url = encodeURIComponent(window.location.href);
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
    let likes = parseInt(likeCount.textContent, 10);
    let dislikes = parseInt(dislikeCount.textContent, 10);
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

    // TODO: POST /api/posts/{id}/vote {value: 1}
});

dislikeBtn.addEventListener('click', () => {
    let likes = parseInt(likeCount.textContent, 10);
    let dislikes = parseInt(dislikeCount.textContent, 10);
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

    // TODO: POST /api/posts/{id}/vote {value: -1}
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
    commentCount.textContent = parseInt(commentCount.textContent, 10) + 1;

    // TODO: POST /api/posts/{id}/comments {text}
    // Si falla: revertir UI y mostrar alerta
});

// ====== (Opcional) Cargar contenido desde la BD al abrir ======
// TODO: GET /api/posts/{id} -> {title, author, date, category, body, images[], videoUrl, documents[], links[]}
// TODO: GET /api/posts/{id}/comments
// TODO: GET /api/posts/{id}/related
