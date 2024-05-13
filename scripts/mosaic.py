from modules.images import read_info_from_image
from modules import script_callbacks
import gradio as gr

from scripts.mos_processing import process_mask


def img2input(img) -> str:
    if img is None:
        return gr.HTML.update(value="")

    info, _ = read_info_from_image(img)
    if info is None:
        return gr.HTML.update(value="")

    info = info.strip().replace("\n", "<br>")

    return gr.HTML.update(
        value=f"""
        <h5>Infotext</h5>
        <p style="
        background: var(--panel-background-fill);
        padding: 1em;
        border-radius: 1em;
        ">{info}</p>
    """
    )


def mos_ui():
    """Main Script for UI Tab"""

    with gr.Blocks() as mos_UI:

        with gr.Row():
            input_img = gr.Image(
                image_mode="RGB",
                label="Input Image",
                sources="upload",
                type="pil",
                show_download_button=False,
                interactive=True,
                height=384,
            )

            output_img = gr.Image(
                image_mode="RGB",
                label="Expanded Image",
                type="pil",
                elem_id="mos_out",
                interactive=False,
                height=384,
            )

            mask = gr.Image(
                image_mode="L",
                label="Inpaint Mask",
                type="pil",
                elem_id="mos_mask",
                interactive=False,
                height=384,
            )

        with gr.Row():
            with gr.Column(scale=1):
                directions = gr.CheckboxGroup(
                    ["up", "right", "down", "left"],
                    value="right",
                    label="Directions",
                    elem_id="mos_dir",
                )
                method = gr.Radio(
                    ["stretch", "mirror"],
                    value="stretch",
                    label="Method",
                    elem_id="mos_mod",
                )

                with gr.Row() as stretch_config:
                    stretch_area = gr.Slider(
                        label="Stretch %",
                        minimum=0.25,
                        maximum=0.75,
                        step=0.05,
                        value=0.50,
                    )
                    stretch_scale = gr.Slider(
                        label="Stretch Ratio", minimum=1, maximum=5, step=1, value=2
                    )

                def on_radio_change(choice):
                    if choice == "stretch":
                        return gr.Row.update(visible=True)
                    else:
                        return gr.Row.update(visible=False)

                method.change(on_radio_change, method, stretch_config)

            with gr.Column(scale=2):
                with gr.Row():
                    with gr.Column():
                        expansion_X = gr.Slider(
                            label="Horizontal Expand %",
                            minimum=0.05,
                            maximum=1.00,
                            step=0.05,
                            value=0.50,
                        )
                        expansion_Y = gr.Slider(
                            label="Vertical Expand %",
                            minimum=0.05,
                            maximum=1.00,
                            step=0.05,
                            value=0.50,
                        )
                        blur = gr.Slider(
                            label="Mask Feathering",
                            minimum=0.0,
                            maximum=64.0,
                            step=4.0,
                            value=0.0,
                        )

                    with gr.Column():
                        steps_S = gr.Slider(
                            label="Short-Side Tile Count",
                            minimum=1,
                            maximum=6,
                            step=1,
                            value=3,
                        )
                        steps_L = gr.Slider(
                            label="Long-Side Tile Count",
                            minimum=12,
                            maximum=72,
                            step=12,
                            value=24,
                        )
                        overlap = gr.Slider(
                            label="Mask Overlap %",
                            minimum=0.05,
                            maximum=0.50,
                            step=0.05,
                            value=0.15,
                        )

                infotext = gr.HTML()

            with gr.Column(scale=1):
                proc_btn = gr.Button("Process Mosaic", variant="primary")
                send_btn = gr.Button("Send to Inpaint", variant="primary")

                with gr.Row():
                    cnet_mode = gr.Radio(["txt", "img"], value="txt", label="Tab")
                    cnet_id = gr.Number(0, label="ControlNet ID", precision=0)
                cnet_send_btn = gr.Button("Send to ControlNet", variant="primary")

                gr.Markdown('<p align="right"><sub>v2.5</sub></p>', elem_id="mos_ver")

        input_img.change(img2input, input_img, infotext)

        proc_btn.click(
            process_mask,
            inputs=[
                input_img,
                directions,
                method,
                stretch_area,
                stretch_scale,
                expansion_X,
                expansion_Y,
                overlap,
                steps_S,
                steps_L,
                blur,
            ],
            outputs=[output_img, mask],
        )

        send_btn.click(None, None, None, _js="() => { mos_img2inpaint(); }")

        cnet_send_btn.click(
            None, [cnet_mode, cnet_id], None, _js="(m, i) => { mos_img2cnet(m, i); }"
        )

        for comp in [
            input_img,
            directions,
            method,
            stretch_area,
            stretch_scale,
            expansion_X,
            expansion_Y,
            overlap,
            steps_S,
            steps_L,
            cnet_mode,
            cnet_id,
        ]:
            comp.do_not_save_to_config = True

    return [(mos_UI, "Mosaic", "sd-webui-mosaic-io")]


script_callbacks.on_ui_tabs(mos_ui)
