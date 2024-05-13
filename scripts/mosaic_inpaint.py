from modules.processing import process_images
import modules.scripts as scripts
from PIL import Image
import gradio as gr
import numpy as np


def _mosaic(img, X, Y) -> Image:
    """Helper function to generate the tiles"""
    downsample = img.resize((X, Y), Image.Resampling.BOX)
    return downsample.resize(img.size, Image.Resampling.NEAREST)


class Mosaic(scripts.Script):
    def title(self):
        return "Mosaic Inpaint"

    def show(self, is_img2img):
        return is_img2img

    def ui(self, is_img2img):
        if not is_img2img:
            return None

        steps_H = gr.Slider(
            label="Horizontal Tile Count", minimum=8, maximum=64, step=8, value=16
        )
        steps_V = gr.Slider(
            label="Vertical Tile Count", minimum=8, maximum=64, step=8, value=16
        )

        blur = gr.Slider(
            label="Mask Overlaps",
            minimum=4,
            maximum=64,
            step=4,
            value=8,
            info="Overrides Mask Blur",
        )

        for comp in [steps_H, steps_V, blur]:
            comp.do_not_save_to_config = True

        return [steps_H, steps_V, blur]

    def run(self, p, steps_H: int, steps_V: int, blur: int):
        assert len(p.init_images) == 1
        mask = getattr(p, "image_mask", None)
        img = p.init_images[0]
        shift = int(blur / 2)

        if p.denoising_strength < 0.75:
            print("High Denoising Strength is recommended!")

        # img2img
        if mask is None:
            img = _mosaic(img, steps_H, steps_V)
            p.init_images[0] = img
            proc = process_images(p)
            proc.images.append(img)
            return proc

        # Inpaint
        else:
            assert mask.mode == "L"
            mask_array = np.array(mask)
            non_zero_pixels = np.nonzero(mask_array)

            try:
                min_y, min_x = np.min(non_zero_pixels, axis=1)
                max_y, max_x = np.max(non_zero_pixels, axis=1)
            except ValueError:
                print("\n\n[Warning] Inpaint with no Mask...\n\n")
                return process_images(p)

            exp_box = (
                max(min_y - shift, 0),
                min(max_y + shift, mask.size[1]),
                max(min_x - shift, 0),
                min(max_x + shift, mask.size[0]),
            )

            x_lim = int((min_x + max_x) / 2)
            y_lim = int((min_y + max_y) / 2)

            img_box = (
                min(min_x + shift, x_lim),
                min(min_y + shift, y_lim),
                max(max_x - shift, x_lim),
                max(max_y - shift, y_lim),
            )

            mosaic = _mosaic(img.crop(img_box), steps_H, steps_V)

            new_mask_array = np.zeros((mask.size[::-1]), dtype=np.uint8)
            new_mask_array[exp_box[0] : exp_box[1], exp_box[2] : exp_box[3]] = 255

            new_mask = Image.fromarray(new_mask_array)

            img.paste(mosaic, img_box)
            p.init_images[0] = img
            p.image_mask = new_mask
            p.mask_blur = blur

            proc = process_images(p)
            proc.images.append(img)
            proc.images.append(new_mask)

            return proc
