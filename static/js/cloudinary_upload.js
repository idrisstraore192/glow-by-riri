function addCloudinaryButton(urlField) {
    if (urlField.dataset.cloudinaryReady) return;
    urlField.dataset.cloudinaryReady = 'true';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = '📤 Uploader une photo';
    btn.style.cssText = 'margin-top:8px; padding:6px 14px; background:#3448c5; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:13px;';
    urlField.parentNode.insertBefore(btn, urlField.nextSibling);

    var preview = document.createElement('img');
    preview.style.cssText = 'display:block; margin-top:10px; max-height:160px; border-radius:4px;';
    if (urlField.value) preview.src = urlField.value;
    btn.parentNode.insertBefore(preview, btn.nextSibling);

    var widget = cloudinary.createUploadWidget({
        cloudName: 'dsyvh6owc',
        uploadPreset: 'glow_products',
        sources: ['local', 'url'],
        multiple: false,
        folder: 'products',
        cropping: false,
    }, function (error, result) {
        if (!error && result && result.event === 'success') {
            urlField.value = result.info.secure_url;
            preview.src = result.info.secure_url;
        }
    });

    btn.addEventListener('click', function () { widget.open(); });
}

function initAllCloudinaryFields() {
    document.querySelectorAll('input[id$="image_url"]').forEach(function(field) {
        addCloudinaryButton(field);
    });
}

document.addEventListener('DOMContentLoaded', initAllCloudinaryFields);

// Gérer les nouvelles lignes ajoutées dynamiquement dans les inlines
document.addEventListener('click', function(e) {
    if (e.target && (e.target.classList.contains('add-row') || e.target.closest('.add-row'))) {
        setTimeout(initAllCloudinaryFields, 300);
    }
});
