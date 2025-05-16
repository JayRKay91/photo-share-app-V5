document.addEventListener('DOMContentLoaded', () => {
    let editMode = false;
    const deleteBtns = Array.from(document.querySelectorAll('.delete-album-btn'));
    const renameBtns = Array.from(document.querySelectorAll('.rename-album-btn'));
    const editBtns = Array.from(document.querySelectorAll('.edit-albums-btn'));

    // Initialize: hide icons
    deleteBtns.forEach(btn => btn.style.display = 'none');
    renameBtns.forEach(btn => btn.style.display = 'none');

    // Toggle edit mode: show/hide delete & rename icons
    const toggleEditMode = () => {
        editMode = !editMode;
        document.body.classList.toggle('edit-mode', editMode);
        deleteBtns.forEach(btn => btn.style.display = editMode ? '' : 'none');
        renameBtns.forEach(btn => btn.style.display = editMode ? '' : 'none');
    };

    // Attach toggle handler
    editBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            toggleEditMode();
        });
    });

    // Handle album deletion
    const handleDelete = (btn) => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const card = btn.closest('.album-card');
            const titleElem = card.querySelector('.album-title');
            const albumTitle = titleElem?.textContent.trim();
            if (!albumTitle) {
                alert('Album title not found.');
                return;
            }
            if (!confirm(`Are you sure you want to delete album "${albumTitle}"?`)) return;

            try {
                const res = await fetch('/delete_album', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ album_title: albumTitle })
                });
                if (!res.ok) {
                    const errorData = await res.json();
                    alert(errorData.error || 'Failed to delete album.');
                    return;
                }
                card.remove();
            } catch (err) {
                console.error(err);
                alert('Network error while deleting album.');
            }
        });
    };

    // Handle album renaming
    const handleRename = (btn) => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const card = btn.closest('.album-card');
            const titleElem = card.querySelector('.album-title');
            const oldTitle = titleElem?.textContent.trim();
            if (!oldTitle) {
                alert('Album title not found.');
                return;
            }
            const newTitle = prompt(`New name for album "${oldTitle}"?`, oldTitle);
            if (!newTitle || newTitle.trim() === '' || newTitle === oldTitle) return;

            try {
                const res = await fetch('/rename_album', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_title: oldTitle, new_title: newTitle })
                });
                if (!res.ok) {
                    const errorData = await res.json();
                    alert(errorData.error || errorData.message || 'Failed to rename album.');
                    return;
                }
                titleElem.textContent = newTitle;
            } catch (err) {
                console.error(err);
                alert('Network error while renaming album.');
            }
        });
    };

    // Attach delete and rename handlers
    deleteBtns.forEach(handleDelete);
    renameBtns.forEach(handleRename);
});
