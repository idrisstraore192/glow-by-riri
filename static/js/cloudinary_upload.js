function addCloudinaryButton(urlField) {
    if (urlField.dataset.cloudinaryReady) return;
    urlField.dataset.cloudinaryReady = 'true';

    // Bouton upload
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = '📤 Uploader des photos';
    btn.style.cssText = 'margin-top:8px; padding:6px 14px; background:#3448c5; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:13px; display:block;';
    urlField.parentNode.insertBefore(btn, urlField.nextSibling);

    // Aperçu
    var preview = document.createElement('img');
    preview.style.cssText = 'display:block; margin-top:10px; max-height:160px; border-radius:4px;';
    if (urlField.value) preview.src = urlField.value;
    btn.parentNode.insertBefore(preview, btn.nextSibling);

    var pendingUrls = [];

    var widget = cloudinary.createUploadWidget({
        cloudName: 'dsyvh6owc',
        uploadPreset: 'glow_products',
        sources: ['local', 'url'],
        multiple: true,
        folder: 'products',
        cropping: false,
    }, function(error, result) {
        if (!error && result && result.event === 'success') {
            pendingUrls.push(result.info.secure_url);
        }
        if (!error && result && result.event === 'close') {
            if (pendingUrls.length === 0) return;

            // Première URL dans le champ actuel
            urlField.value = pendingUrls[0];
            preview.src = pendingUrls[0];

            // URLs supplémentaires → nouvelles lignes inline
            if (pendingUrls.length > 1) {
                var addLink = findAddRowLink(urlField);
                fillNextRows(addLink, pendingUrls, 1);
            }
            pendingUrls = [];
        }
    });

    btn.addEventListener('click', function() { widget.open(); });
}

function findAddRowLink(urlField) {
    var el = urlField;
    while (el && !el.classList.contains('inline-group')) {
        el = el.parentElement;
    }
    return el ? el.querySelector('.add-row a') : null;
}

function fillNextRows(addLink, urls, index) {
    if (!addLink || index >= urls.length) return;
    addLink.click();
    setTimeout(function() {
        // Chercher le premier champ image_url vide (peu importe cloudinaryReady)
        var emptyFields = Array.from(document.querySelectorAll('input[id*="image_url"]'))
            .filter(function(f) { return f.value === ''; });
        if (emptyFields.length > 0) {
            var field = emptyFields[emptyFields.length - 1];
            field.value = urls[index];
            // Mettre à jour l'aperçu existant si présent
            var existingPreview = field.parentNode.querySelector('img');
            if (existingPreview) {
                existingPreview.src = urls[index];
            } else {
                var prev = document.createElement('img');
                prev.style.cssText = 'display:block; margin-top:10px; max-height:160px; border-radius:4px;';
                prev.src = urls[index];
                field.parentNode.appendChild(prev);
            }
        }
        fillNextRows(addLink, urls, index + 1);
    }, 500);
}

function initAllCloudinaryFields() {
    document.querySelectorAll('input[id*="image_url"]').forEach(function(field) {
        addCloudinaryButton(field);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initAllCloudinaryFields();

    // Détecter les nouvelles lignes ajoutées via "Ajouter"
    document.querySelectorAll('.add-row a').forEach(function(link) {
        link.addEventListener('click', function() {
            setTimeout(initAllCloudinaryFields, 400);
        });
    });
});
