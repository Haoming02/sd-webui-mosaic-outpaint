"""Headless API for mosaic-outpaint auto-expand geometry.

Exposes ``POST /mosaic/prepare`` which auto-expands an input image to a target
canvas size (centred, mirror/stretch + mosaic borders) and returns the expanded
canvas plus the inpaint mask (white = new border area to repaint). Generation
itself is done by the caller via ``/sdapi/v1/img2img`` inpaint. Pure geometry,
no model — safe and deterministic.

Added so the Mosaic tab's "Auto Expand to target width/height" becomes usable
headless (e.g. from the forge-gen MCP bridge). Does not touch the existing UI.
"""
import base64
import io

from modules import script_callbacks

# Import at module load time: Forge points sys.path at THIS extension's scripts/
# dir during load, so ``scripts.mos_processing`` resolves correctly here (same
# way mosaic.py imports it). Capture the reference for use at request time.
from scripts.mos_processing import process_mask_by_target_size


def _b64_to_pil(value: str):
    from PIL import Image
    if value.startswith("data:") and "," in value:
        value = value.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(value))).convert("RGB")


def _pil_to_b64(img, mode: str | None = None) -> str:
    if mode is not None:
        img = img.convert(mode)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _on_app_started(_demo, app):
    from fastapi import Body
    from fastapi.responses import JSONResponse

    @app.post("/mosaic/prepare")
    def mosaic_prepare(payload: dict = Body(...)):
        try:
            image = payload.get("image")
            if not image:
                return JSONResponse({"error": "missing 'image'"}, status_code=400)
            target_w = int(payload.get("target_width", payload.get("target_w")))
            target_h = int(payload.get("target_height", payload.get("target_h")))
            method = payload.get("method", "mirror")
            stretch_area = float(payload.get("stretch_area", 0.5))
            stretch_scale = int(payload.get("stretch_scale", 2))
            overlap = float(payload.get("overlap", 0.15))
            steps_S = int(payload.get("steps_S", 3))
            steps_L = int(payload.get("steps_L", 24))
            blur = float(payload.get("blur", 0.0))

            src = _b64_to_pil(image)
            canvas, mask = process_mask_by_target_size(
                src, target_w, target_h, method, stretch_area, stretch_scale,
                overlap, steps_S, steps_L, blur,
            )
            return {
                "expanded_image": _pil_to_b64(canvas),
                "mask": _pil_to_b64(mask, mode="L"),
                "width": canvas.width,
                "height": canvas.height,
            }
        except Exception as e:  # surface a clean error instead of a 500 HTML page
            return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=400)


script_callbacks.on_app_started(_on_app_started)
