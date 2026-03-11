import gradio as gr
from PIL import Image, ImageFilter, ImageOps


def _mosaic(img: Image.Image, x: int, y: int) -> Image.Image:
    """Helper function to generate the tiles"""
    downsample = img.resize((x, y), Image.Resampling.BOX)
    return downsample.resize(img.size, Image.Resampling.NEAREST)


def generate_mosaic(
    input_img: Image.Image,
    UP: bool,
    RIGHT: bool,
    DOWN: bool,
    LEFT: bool,
    width: int,
    height: int,
    exp_x: int,
    exp_y: int,
    steps_S: int,
    steps_L: int,
) -> Image.Image:
    """Convert the expanded border(s) into mosaic tiles"""
    new_width, new_height = input_img.size
    steps_C = int((steps_S + steps_L) / 2)

    lx = exp_x if LEFT else 0
    rx = width + lx
    uy = exp_y if UP else 0
    dy = height + uy

    if UP and LEFT:
        corner = input_img.crop((0, 0, lx, exp_y))
        corner = _mosaic(corner, steps_C, steps_C)
        input_img.paste(corner, (0, 0))

    if UP:
        edge = input_img.crop((lx, 0, rx, exp_y))
        edge = _mosaic(edge, steps_L, steps_S)
        input_img.paste(edge, (lx, 0))

    if UP and RIGHT:
        corner = input_img.crop((rx, 0, new_width, exp_y))
        corner = _mosaic(corner, steps_C, steps_C)
        input_img.paste(corner, (rx, 0))

    if LEFT:
        edge = input_img.crop((0, uy, exp_x, dy))
        edge = _mosaic(edge, steps_S, steps_L)
        input_img.paste(edge, (0, uy))

    if RIGHT:
        edge = input_img.crop((rx, uy, new_width, dy))
        edge = _mosaic(edge, steps_S, steps_L)
        input_img.paste(edge, (rx, uy))

    if DOWN and LEFT:
        corner = input_img.crop((0, dy, lx, new_height))
        corner = _mosaic(corner, steps_C, steps_C)
        input_img.paste(corner, (0, dy))

    if DOWN:
        edge = input_img.crop((lx, dy, rx, new_height))
        edge = _mosaic(edge, steps_L, steps_S)
        input_img.paste(edge, (lx, dy))

    if DOWN and RIGHT:
        corner = input_img.crop((rx, dy, new_width, new_height))
        corner = _mosaic(corner, steps_C, steps_C)
        input_img.paste(corner, (rx, dy))

    return input_img


def preprocess_image(
    input_img: Image.Image,
    UP: bool,
    RIGHT: bool,
    DOWN: bool,
    LEFT: bool,
    width: int,
    height: int,
    exp_x: int,
    exp_y: int,
) -> Image.Image:
    """Mirror the input image in the specified direction(s)"""
    H = sum([RIGHT, LEFT])
    V = sum([UP, DOWN])

    canvas = Image.new("RGB", (width * (H + 1), height * (V + 1)))
    temp = Image.new("RGB", (width * (H + 1), height))

    if H > 0:
        FLIP_H = ImageOps.mirror(input_img)

        if LEFT:
            temp.paste(FLIP_H, (0, 0))
            temp.paste(input_img, (width, 0))
            if RIGHT:
                temp.paste(FLIP_H, (width * 2, 0))
        else:
            temp.paste(input_img, (0, 0))
            temp.paste(FLIP_H, (width, 0))
    else:
        temp = input_img

    if V > 0:
        FLIP_V = ImageOps.flip(temp)

        if UP:
            canvas.paste(FLIP_V, (0, 0))
            canvas.paste(temp, (0, height))
            if DOWN:
                canvas.paste(FLIP_V, (0, height * 2))
        else:
            canvas.paste(temp, (0, 0))
            canvas.paste(FLIP_V, (0, height))
    else:
        canvas = temp

    x1 = (width - exp_x) if LEFT else 0
    y1 = (height - exp_y) if UP else 0
    x2 = ((width + exp_x) if RIGHT else width) + (width if LEFT else 0)
    y2 = ((height + exp_y) if DOWN else height) + (height if UP else 0)

    return canvas.crop((x1, y1, x2, y2))


def stretch_image(
    input_img: Image.Image,
    stretch_area: float,
    stretch_scale: int,
    UP: bool,
    RIGHT: bool,
    DOWN: bool,
    LEFT: bool,
    width: int,
    height: int,
    exp_x: int,
    exp_y: int,
) -> Image.Image:
    """Stretch the {area} amount of image by {scale} to blur out the border"""
    new_width, new_height = input_img.size

    str_x = int(exp_x * stretch_area)
    str_y = int(exp_y * stretch_area)
    str_ed_x = exp_x * stretch_scale
    str_ed_y = exp_y * stretch_scale

    if LEFT:
        edge = input_img.crop((exp_x - str_x, 0, exp_x, new_height))
        edge = edge.resize((str_ed_x, new_height), Image.Resampling.BILINEAR)
        edge = edge.crop((str_ed_x - exp_x, 0, str_ed_x, new_height))
        input_img.paste(edge, (0, 0))

    if RIGHT:
        ix = width + (exp_x if LEFT else 0)
        edge = input_img.crop((ix, 0, ix + str_x, new_height))
        edge = edge.resize((str_ed_x, new_height), Image.Resampling.BILINEAR)
        edge = edge.crop((0, 0, exp_x, new_height))
        input_img.paste(edge, (ix, 0))

    if UP:
        edge = input_img.crop((0, exp_y - str_y, new_width, exp_y))
        edge = edge.resize((new_width, str_ed_y), Image.Resampling.BILINEAR)
        edge = edge.crop((0, str_ed_y - exp_y, new_width, str_ed_y))
        input_img.paste(edge, (0, 0))

    if DOWN:
        iy = height + (exp_y if UP else 0)
        edge = input_img.crop((0, iy, new_width, iy + str_y))
        edge = edge.resize((new_width, str_ed_y), Image.Resampling.BILINEAR)
        edge = edge.crop((0, 0, new_width, exp_y))
        input_img.paste(edge, (0, iy))

    return input_img


def process_mask(
    input_img: Image.Image,
    directions: list,
    method: str,
    stretch_area: float,
    stretch_scale: int,
    expansion_X: float,
    expansion_Y: float,
    overlap: float,
    steps_S: int,
    steps_L: int,
    blur: float,
) -> list[Image.Image]:
    """Main Function"""
    if input_img is None:
        return [None, None]

    UP: bool = "up" in directions
    RIGHT: bool = "right" in directions
    DOWN: bool = "down" in directions
    LEFT: bool = "left" in directions

    DIRS = (UP, RIGHT, DOWN, LEFT)

    if not any(DIRS):
        return [None, None]

    OG_SIZE = (width, height) = input_img.size

    exp_x = int(width * expansion_X)
    exp_y = int(height * expansion_Y)
    EXP_SIZE = (exp_x, exp_y)

    input_img = preprocess_image(input_img, *DIRS, *OG_SIZE, *EXP_SIZE)

    if method == "stretch":
        input_img = stretch_image(
            input_img, stretch_area, stretch_scale, *DIRS, *OG_SIZE, *EXP_SIZE
        )

    mask = Image.new("L", input_img.size, 255)
    H = sum([RIGHT, LEFT])
    V = sum([UP, DOWN])

    block = Image.new(
        "L", (int(width * (1.0 - (overlap * H))), int(height * (1.0 - (overlap * V))))
    )

    mask.paste(
        block,
        (
            0 if not LEFT else exp_x + int(width * overlap),
            0 if not UP else exp_y + int(height * overlap),
        ),
    )

    if blur > 0.0:
        mask = mask.filter(ImageFilter.BoxBlur(blur))

    return [
        generate_mosaic(input_img, *DIRS, *OG_SIZE, *EXP_SIZE, steps_S, steps_L),
        mask,
    ]


# ---------------------------------------------------------------------------
# Auto-Expand by Target Size
# ---------------------------------------------------------------------------

def _fill_borders_mirror(
    orig: Image.Image,
    pad_l: int,
    pad_t: int,
    pad_r: int,
    pad_b: int,
) -> Image.Image:
    """Fill a canvas by mirroring the original image edges outward."""
    OW, OH = orig.size
    TW = pad_l + OW + pad_r
    TH = pad_t + OH + pad_b
    canvas = Image.new("RGB", (TW, TH))
    canvas.paste(orig, (pad_l, pad_t))

    if pad_l > 0:
        strip = orig.crop((0, 0, min(pad_l, OW), OH))
        strip = ImageOps.mirror(strip).resize((pad_l, OH), Image.Resampling.BILINEAR)
        canvas.paste(strip, (0, pad_t))

    if pad_r > 0:
        strip = orig.crop((max(0, OW - pad_r), 0, OW, OH))
        strip = ImageOps.mirror(strip).resize((pad_r, OH), Image.Resampling.BILINEAR)
        canvas.paste(strip, (pad_l + OW, pad_t))

    mid = canvas.crop((0, pad_t, TW, pad_t + OH))

    if pad_t > 0:
        row = mid.crop((0, 0, TW, min(pad_t, OH)))
        row = ImageOps.flip(row).resize((TW, pad_t), Image.Resampling.BILINEAR)
        canvas.paste(row, (0, 0))

    if pad_b > 0:
        row = mid.crop((0, max(0, OH - pad_b), TW, OH))
        row = ImageOps.flip(row).resize((TW, pad_b), Image.Resampling.BILINEAR)
        canvas.paste(row, (0, pad_t + OH))

    return canvas


def _fill_borders_stretch(
    orig: Image.Image,
    pad_l: int,
    pad_t: int,
    pad_r: int,
    pad_b: int,
    stretch_area: float,
    stretch_scale: int,
) -> Image.Image:
    """Fill a canvas by stretching the original image edges outward."""
    OW, OH = orig.size
    TW = pad_l + OW + pad_r
    TH = pad_t + OH + pad_b
    canvas = Image.new("RGB", (TW, TH))
    canvas.paste(orig, (pad_l, pad_t))

    sample_x = max(4, int(OW * stretch_area))
    sample_y = max(4, int(OH * stretch_area))

    if pad_l > 0:
        strip = orig.crop((0, 0, sample_x, OH))
        stretched_w = sample_x * stretch_scale + pad_l
        strip = strip.resize((stretched_w, OH), Image.Resampling.BILINEAR)
        strip = strip.crop((stretched_w - pad_l, 0, stretched_w, OH))
        canvas.paste(strip, (0, pad_t))

    if pad_r > 0:
        strip = orig.crop((OW - sample_x, 0, OW, OH))
        stretched_w = sample_x * stretch_scale + pad_r
        strip = strip.resize((stretched_w, OH), Image.Resampling.BILINEAR)
        strip = strip.crop((0, 0, pad_r, OH))
        canvas.paste(strip, (pad_l + OW, pad_t))

    mid = canvas.crop((0, pad_t, TW, pad_t + OH))

    if pad_t > 0:
        row = mid.crop((0, 0, TW, sample_y))
        stretched_h = sample_y * stretch_scale + pad_t
        row = row.resize((TW, stretched_h), Image.Resampling.BILINEAR)
        row = row.crop((0, stretched_h - pad_t, TW, stretched_h))
        canvas.paste(row, (0, 0))

    if pad_b > 0:
        row = mid.crop((0, OH - sample_y, TW, OH))
        stretched_h = sample_y * stretch_scale + pad_b
        row = row.resize((TW, stretched_h), Image.Resampling.BILINEAR)
        row = row.crop((0, 0, TW, pad_b))
        canvas.paste(row, (0, pad_t + OH))

    return canvas


def _apply_border_mosaic(
    canvas: Image.Image,
    pad_l: int,
    pad_t: int,
    pad_r: int,
    pad_b: int,
    steps_S: int,
    steps_L: int,
) -> Image.Image:
    """Apply mosaic tiles to the border regions of the canvas."""
    TW, TH = canvas.size
    OH = TH - pad_t - pad_b

    if pad_t > 0:
        region = canvas.crop((0, 0, TW, pad_t))
        canvas.paste(_mosaic(region, steps_L, steps_S), (0, 0))

    if pad_b > 0:
        region = canvas.crop((0, TH - pad_b, TW, TH))
        canvas.paste(_mosaic(region, steps_L, steps_S), (0, TH - pad_b))

    if pad_l > 0:
        region = canvas.crop((0, pad_t, pad_l, pad_t + OH))
        canvas.paste(_mosaic(region, steps_S, steps_L), (0, pad_t))

    if pad_r > 0:
        region = canvas.crop((TW - pad_r, pad_t, TW, pad_t + OH))
        canvas.paste(_mosaic(region, steps_S, steps_L), (TW - pad_r, pad_t))

    return canvas


def process_mask_by_target_size(
    input_img: Image.Image,
    target_w: int,
    target_h: int,
    method: str,
    stretch_area: float,
    stretch_scale: int,
    overlap: float,
    steps_S: int,
    steps_L: int,
    blur: float,
) -> list:
    """Auto-expand image to target size (centred) with mosaic borders + inpaint mask.
    If the source image is larger than the target in any dimension, it is scaled
    down (keeping aspect ratio) to fit inside the target before centering.
    """
    if input_img is None:
        raise gr.Error("Auto-Expand: No input image provided.")

    try:
        target_w = int(target_w)
        target_h = int(target_h)
    except (TypeError, ValueError):
        raise gr.Error("Auto-Expand: Target width / height must be valid integers.")

    if target_w < 1 or target_h < 1:
        raise gr.Error("Auto-Expand: Target dimensions must be at least 1 px.")

    OW, OH = input_img.size

    # Scale down if the image does not fit inside the target (preserve aspect ratio)
    scale = min(target_w / OW, target_h / OH)
    if scale < 1.0:
        new_w = max(1, round(OW * scale))
        new_h = max(1, round(OH * scale))
        input_img = input_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        OW, OH = input_img.size
        gr.Warning(
            f"Auto-Expand: Image was scaled down from original size to {OW}\u00d7{OH} "
            f"to fit within the target {target_w}\u00d7{target_h}."
        )

    if target_w == OW and target_h == OH:
        return [input_img.copy(), Image.new("L", (OW, OH), 0)]

    pad_l = (target_w - OW) // 2
    pad_r = target_w - OW - pad_l
    pad_t = (target_h - OH) // 2
    pad_b = target_h - OH - pad_t

    if method == "stretch":
        canvas = _fill_borders_stretch(
            input_img, pad_l, pad_t, pad_r, pad_b, stretch_area, stretch_scale
        )
    else:
        canvas = _fill_borders_mirror(input_img, pad_l, pad_t, pad_r, pad_b)

    canvas = _apply_border_mosaic(canvas, pad_l, pad_t, pad_r, pad_b, steps_S, steps_L)

    mask = Image.new("L", (target_w, target_h), 255)
    inset_l = int(pad_l * overlap) if pad_l > 0 else 0
    inset_r = int(pad_r * overlap) if pad_r > 0 else 0
    inset_t = int(pad_t * overlap) if pad_t > 0 else 0
    inset_b = int(pad_b * overlap) if pad_b > 0 else 0

    inner_w = max(1, OW - inset_l - inset_r)
    inner_h = max(1, OH - inset_t - inset_b)
    block = Image.new("L", (inner_w, inner_h), 0)
    mask.paste(block, (pad_l + inset_l, pad_t + inset_t))

    if blur > 0.0:
        mask = mask.filter(ImageFilter.BoxBlur(blur))

    return [canvas, mask]
