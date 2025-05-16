// static/js/gallery.js
'use strict';

const preview      = document.getElementById('preview');
const previewBox   = document.querySelector('#preview .preview-box');
let mediaList = [];
let currentIndex = 0;

function populateMediaList() {
  mediaList = Array.from(document.querySelectorAll('img.clickable[data-full]'))
    .map(el => ({
      src: el.dataset.full,
      type: el.dataset.type || 'image'
    }));
}

function openPreviewAt(index) {
  currentIndex = (index + mediaList.length) % mediaList.length;
  showPreview();
  preview.style.display = 'flex';
}

function showPreview() {
  previewBox.innerHTML = '';
  const { src, type } = mediaList[currentIndex];
  let content;
  if (type === 'video') {
    content = document.createElement('video');
    content.src = src;
    content.controls = true;
    content.autoplay = true;
    content.playsInline = true;
  } else {
    content = document.createElement('img');
    content.src = src;
    content.alt = '';
  }
  content.className = 'preview-content';
  previewBox.appendChild(content);
}

function navigate(offset) {
  openPreviewAt(currentIndex + offset);
}

function closePreview() {
  preview.style.display = 'none';
  previewBox.innerHTML = '';
}

function handleError(imgElement) {
  const fallbackUrl = imgElement.dataset.full;
  const filename = fallbackUrl.split('/').pop();
  const link = document.createElement('a');
  link.href = fallbackUrl;
  link.textContent = filename;
  link.target = '_blank';
  imgElement.parentNode.replaceChild(link, imgElement);
}

// ✅ FIXED: submitForm is now in global scope
function submitForm(formId) {
  const form = document.getElementById(formId);
  if (form) {
    form.submit();
  } else {
    console.error("Form not found:", formId);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  populateMediaList();
  document.querySelectorAll('img.clickable[data-full]').forEach((img, idx) => {
    img.addEventListener('click', () => openPreviewAt(idx));
  });

  // Add arrow button click listeners
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');

  if (prevBtn && nextBtn) {
    prevBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      navigate(-1);
    });

    nextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      navigate(1);
    });
  }

  // ⭐ Favorite album toggle with backend persistence
  document.querySelectorAll(".favorite-toggle").forEach(button => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const album = this.dataset.album;
      if (!album) {
        console.error("No album specified on button");
        return;
      }

      const formData = new FormData();
      formData.append('album', album);

      fetch('/toggle_favorite_album', {
        method: 'POST',
        body: formData
      })
      .then(response => {
        if (!response.ok) throw new Error("Network response was not ok");
        return response.json();
      })
      .then(data => {
        if (data.status === "success") {
          if (data.action === "favorited") {
            this.classList.add("favorited");
            this.textContent = "★";
          } else {
            this.classList.remove("favorited");
            this.textContent = "☆";
          }
        } else {
          console.error("Toggle favorite error:", data.message);
        }
      })
      .catch(err => {
        console.error("Fetch error in favoriting:", err);
      });
    });
  });
});

document.addEventListener('click', function (e) {
  if (e.target.matches('.tag-delete-btn')) {
    e.preventDefault();
    const button = e.target;
    const formId = button.dataset.form;
    const form = document.getElementById(formId);

    if (!form) return console.error("Form not found:", formId);

    const url = form.action;
    const formData = new FormData(form);

    fetch(url, {
      method: 'POST',
      body: formData,
    })
    .then(response => {
      if (!response.ok) throw new Error("Failed to delete tag");
      // Remove tag from DOM
      const tagSpan = button.closest('.tag-label');
      if (tagSpan) tagSpan.remove();
    })
    .catch(err => {
      console.error("Tag deletion error:", err);
    });
  }
});

document.addEventListener('keydown', (e) => {
  if (preview.style.display === 'flex') {
    if (e.key === 'Escape') {
      closePreview();
    } else if (e.key === 'ArrowRight') {
      navigate(1);
    } else if (e.key === 'ArrowLeft') {
      navigate(-1);
    }
  }
});
