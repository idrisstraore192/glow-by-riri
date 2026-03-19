// ── Bouton PHOTOS ──────────────────────────────────────────────
function addCloudinaryButton(urlField) {
    if (urlField.dataset.cloudinaryReady) return;
    urlField.dataset.cloudinaryReady = 'true';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = '📷 Uploader des photos';
    btn.style.cssText = 'margin-top:8px; padding:6px 14px; background:#3448c5; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:13px; display:block;';
    urlField.parentNode.insertBefore(btn, urlField.nextSibling);

    var preview = document.createElement('img');
    preview.style.cssText = 'display:block; margin-top:10px; max-height:160px; border-radius:4px;';
    if (urlField.value) preview.src = urlField.value;
    btn.parentNode.insertBefore(preview, btn.nextSibling);

    btn.addEventListener('click', function() {
        var pendingUrls = [];

        var widget = cloudinary.createUploadWidget({
            cloudName: 'dsyvh6owc',
            uploadPreset: 'glow_products',
            sources: ['local', 'url'],
            multiple: true,
            folder: 'products',
            cropping: false,
            resourceType: 'image',
            clientAllowedFormats: ['jpg', 'jpeg', 'png', 'webp', 'gif'],
        }, function(error, result) {
            if (!error && result && result.event === 'success') {
                pendingUrls.push(result.info.secure_url);
            }
            if (!error && result && result.event === 'close') {
                widget.destroy();
                if (pendingUrls.length === 0) return;

                urlField.value = pendingUrls[0];
                preview.src = pendingUrls[0];

                if (pendingUrls.length > 1) {
                    var addLink = findAddRowLink(urlField);
                    fillNextRows(addLink, pendingUrls, 1);
                }
            }
        });

        widget.open();
    });
}

// ── Bouton VIDÉO ───────────────────────────────────────────────
function addCloudinaryVideoButton(videoField) {
    if (videoField.dataset.cloudinaryVideoReady) return;
    videoField.dataset.cloudinaryVideoReady = 'true';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = '🎥 Uploader des vidéos';
    btn.style.cssText = 'margin-top:8px; padding:6px 14px; background:#7c3aed; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:13px; display:block;';
    videoField.parentNode.insertBefore(btn, videoField.nextSibling);

    var preview = document.createElement('video');
    preview.controls = true;
    preview.style.cssText = 'display:none; margin-top:10px; max-width:320px; max-height:200px; border-radius:4px;';
    if (videoField.value) {
        preview.src = videoField.value;
        preview.style.display = 'block';
    }
    btn.parentNode.insertBefore(preview, btn.nextSibling);

    btn.addEventListener('click', function() {
        var pendingUrls = [];

        var widget = cloudinary.createUploadWidget({
            cloudName: 'dsyvh6owc',
            uploadPreset: 'glow_products',
            sources: ['local', 'url'],
            multiple: true,
            folder: 'products/videos',
            cropping: false,
            resourceType: 'video',
            clientAllowedFormats: ['mp4', 'mov', 'avi', 'webm'],
        }, function(error, result) {
            if (!error && result && result.event === 'success') {
                pendingUrls.push(result.info.secure_url);
            }
            if (!error && result && result.event === 'close') {
                widget.destroy();
                if (pendingUrls.length === 0) return;

                videoField.value = pendingUrls[0];
                preview.src = pendingUrls[0];
                preview.style.display = 'block';

                if (pendingUrls.length > 1) {
                    var addLink = findAddRowLink(videoField);
                    fillNextVideoRows(addLink, pendingUrls, 1);
                }
            }
        });

        widget.open();
    });
}

// ── Helpers ────────────────────────────────────────────────────
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
        var emptyFields = Array.from(document.querySelectorAll('input[id*="image_url"]'))
            .filter(function(f) { return f.value === ''; });
        if (emptyFields.length > 0) {
            var field = emptyFields[emptyFields.length - 1];
            field.value = urls[index];
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

function fillNextVideoRows(addLink, urls, index) {
    if (!addLink || index >= urls.length) return;
    addLink.click();
    setTimeout(function() {
        var emptyFields = Array.from(document.querySelectorAll('input[id*="video_url"]'))
            .filter(function(f) { return f.value === ''; });
        if (emptyFields.length > 0) {
            var field = emptyFields[emptyFields.length - 1];
            field.value = urls[index];
            var existingPreview = field.parentNode.querySelector('video');
            if (existingPreview) {
                existingPreview.src = urls[index];
                existingPreview.style.display = 'block';
            } else {
                var prev = document.createElement('video');
                prev.controls = true;
                prev.style.cssText = 'display:block; margin-top:10px; max-width:320px; max-height:200px; border-radius:4px;';
                prev.src = urls[index];
                field.parentNode.appendChild(prev);
            }
        }
        fillNextVideoRows(addLink, urls, index + 1);
    }, 500);
}

// ── Init ───────────────────────────────────────────────────────
function initAllCloudinaryFields() {
    document.querySelectorAll('input[id*="image_url"]').forEach(function(field) {
        addCloudinaryButton(field);
    });
    document.querySelectorAll('input[id*="video_url"]').forEach(function(field) {
        addCloudinaryVideoButton(field);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initAllCloudinaryFields();

    document.querySelectorAll('.add-row a').forEach(function(link) {
        link.addEventListener('click', function() {
            setTimeout(initAllCloudinaryFields, 400);
        });
    });
});
