function mos_img2inpaint() {
    const img = gradioApp().getElementById('mos_out').querySelector('img');
    const mask = gradioApp().getElementById('mos_mask').querySelector('img');

    if (img == null || mask == null)
        return;

    const imageInputs = gradioApp().getElementById('img2img_inpaint_upload_tab').querySelectorAll("input[type='file']");
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;

    ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);

    canvas.toBlob((blob) => {
        const file = new File(([blob]), "img.png");
        mos_SetImage(imageInputs[0], file);
    });

    ctx.drawImage(mask, 0, 0, mask.naturalWidth, mask.naturalHeight);

    canvas.toBlob((blob) => {
        const file = new File(([blob]), "mask.png");
        mos_SetImage(imageInputs[1], file);
    });

    switch_to_img2img_tab(4);

    canvas.remove();
}

function mos_img2cnet(mode, id) {
    const img = gradioApp().getElementById('mos_out').querySelector('img');
    const mask = gradioApp().getElementById('mos_mask').querySelector('img');

    if (img == null || mask == null)
        return;

    var cnet_image = null;
    var cnet_mask = null;

    try {
        cnet_image = gradioApp().getElementById(`${mode}2img_controlnet_ControlNet-${id}_input_image`);
        cnet_mask = gradioApp().getElementById(`${mode}2img_controlnet_ControlNet-${id}_mask_image`);
    }
    catch {
        alert('Invalid ControlNet ID');
        return;
    }

    if (mode === 'img') {
        const cb = gradioApp().getElementById(`img2img_controlnet_ControlNet-${id}_controlnet_same_img2img_checkbox`).querySelector("input[type='checkbox']");
        cb.checked = true;
        updateInput(cb);
    }

    const m_cb = gradioApp().getElementById(`${mode}2img_controlnet_ControlNet-${id}_controlnet_mask_upload_checkbox`).querySelector("input[type='checkbox']");
    m_cb.checked = true;
    updateInput(m_cb);

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;

    ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);

    canvas.toBlob((blob) => {
        const file = new File(([blob]), "img.png");
        mos_SetImage(cnet_image, file);
    });

    ctx.drawImage(mask, 0, 0, mask.naturalWidth, mask.naturalHeight);

    canvas.toBlob((blob) => {
        const file = new File(([blob]), "mask.png");
        mos_SetImage(cnet_mask, file);
    });

    if (mode === 'txt')
        switch_to_txt2img();
    else
        switch_to_img2img();

    canvas.remove();
}

function mos_SetImage(cnet, file) {
    const imageInput = cnet.querySelector("input[type='file']");
    const dt = new DataTransfer();
    dt.items.add(file);

    const list = dt.files;
    imageInput.files = list;

    imageInput.dispatchEvent(new Event('change', {
        'bubbles': true,
        "composed": true
    }));

    const observer = new IntersectionObserver((entries, observer) => {
        if (entries[0].intersectionRatio > 0) {
            setTimeout(() => {
                const clear_btn = cnet.querySelector("button[aria-label='Clear']");
                clear_btn.click();
            }, 50);
            observer.disconnect()
        }
    }, { root: document.documentElement });

    observer.observe(cnet);
}

onUiLoaded(async () => {
    const ver = document.getElementById('mos_ver');
    ver.style.marginTop = 'auto';

    const mode = document.getElementById('mos_mod').lastElementChild;
    mode.style.justifyContent = 'center';

    const dirs = document.getElementById('mos_dir').lastElementChild;
    dirs.style.flexDirection = 'column';
    dirs.style.alignItems = 'center';

    const div = document.createElement('div');
    div.style.display = 'flex';
    div.appendChild(dirs.childNodes[3]);
    div.appendChild(dirs.childNodes[1]);

    dirs.insertBefore(div, dirs.lastChild);
});
