function initFotos() {
    document.querySelectorAll('.foto-input').forEach(input => {
        input.addEventListener('change', handleFotoChange);
    });
}

function handleFotoChange() {
    const previewDiv = this.closest('.question-card')?.querySelector('.foto-preview')
        || this.parentElement.querySelector('.foto-preview');

    if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'foto-preview img-thumbnail mt-2';
            if (previewDiv) {
                previewDiv.src = e.target.result;
            } else {
                const container = document.createElement('div');
                container.className = 'foto-preview';
                container.appendChild(img);
                this.parentElement.appendChild(container);
            }
        }.bind(this);
        reader.readAsDataURL(this.files[0]);

        // Upload
        const formData = new FormData();
        formData.append('foto', this.files[0]);

        fetch(`/audit/${SESSION_ID}/upload-foto`, {
            method: 'POST',
            body: formData
        })
        .then(resp => resp.json())
        .then(result => {
            if (result.ok) {
                this.dataset.uploadedPath = result.path;
            }
        })
        .catch(err => console.error('Erro upload:', err));
    }
}
