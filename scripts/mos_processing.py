from PIL import Image, ImageOps, ImageFilter


def _mosaic(img, X, Y) -> Image:
    """Helper function to generate the tiles"""
    downsample = img.resize((X, Y), Image.Resampling.BOX)
    return downsample.resize(img.size, Image.Resampling.NEAREST)


def generate_mosaic(
    input_img: Image,
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
) -> Image:
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
    input_img: Image,
    UP: bool,
    RIGHT: bool,
    DOWN: bool,
    LEFT: bool,
    width: int,
    height: int,
    exp_x: int,
    exp_y: int,
) -> Image:
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
    input_img: Image,
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
) -> Image:
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
    input_img: Image,
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
) -> list:
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
