import gradio as gr
from scripts.mos_processing import process_mask, process_mask_by_target_size

from modules import script_callbacks
from modules.images import read_info_from_image


def img2input(img) -> str:
    if img is None:
        return gr.update(value="")

    info, _ = read_info_from_image(img)
    if info is None:
        return gr.update(value="")

    info = info.strip().replace("\n", "<br>")

    return gr.update(
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
            # ---- Left column: direction / method / stretch ----
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

            # ---- Middle column: shared sliders + auto-expand inputs ----
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

                auto_expand_chk = gr.Checkbox(label="Auto Expand", value=False)

                with gr.Row():
                    target_w = gr.Number(
                        label="Target Width",
                        value=1024,
                        precision=0,
                        minimum=1,
                        scale=3,
                    )
                    swap_btn = gr.Button("⇄", scale=1, size="sm", min_width=40)
                    target_h = gr.Number(
                        label="Target Height",
                        value=1024,
                        precision=0,
                        minimum=1,
                        scale=3,
                    )
                    get_size_btn = gr.Button("Get Current Image Size", scale=3, size="sm")

            # ---- Right column: action buttons ----
            with gr.Column(scale=1):
                proc_btn = gr.Button("Process Mosaic", variant="primary")

                gr.Markdown("---")

                with gr.Row():
                    send_btn = gr.Button("Send to Inpaint", variant="primary")
                    send_m_btn = gr.Button("Send to Inpaint Upload", variant="primary")

                with gr.Row():
                    cnet_mode = gr.Radio(["txt", "img"], value="txt", label="Tab")
                    cnet_id = gr.Number(0, label="ControlNet ID", precision=0)
                cnet_send_btn = gr.Button("Send to ControlNet", variant="primary")

                gr.Markdown('<p align="right"><sub>v2.8</sub></p>', elem_id="mos_ver")

        # ---- Infotext at the bottom (full width) ----
        infotext = gr.HTML()

        # ---- Event bindings ----
        def get_image_size(img):
            if img is None:
                return gr.update(), gr.update()
            w, h = img.size
            return gr.update(value=w), gr.update(value=h)

        def swap_size(w, h):
            return h, w

        def process_unified(
            img, auto_expand, dirs, meth, s_area, s_scale,
            exp_x, exp_y, ovlp, st_s, st_l, bl,
            tgt_w, tgt_h,
        ):
            """Dispatch to auto-expand by target size or normal directional expand."""
            if auto_expand:
                return process_mask_by_target_size(
                    img, tgt_w, tgt_h, meth, s_area, s_scale,
                    ovlp, st_s, st_l, bl,
                )
            else:
                return process_mask(
                    img, dirs, meth, s_area, s_scale,
                    exp_x, exp_y, ovlp, st_s, st_l, bl,
                )

        get_size_btn.click(
            fn=get_image_size,
            inputs=[input_img],
            outputs=[target_w, target_h],
        )

        swap_btn.click(
            fn=swap_size,
            inputs=[target_w, target_h],
            outputs=[target_w, target_h],
        )

        input_img.change(fn=img2input, inputs=[input_img], outputs=[infotext])

        proc_btn.click(
            fn=process_unified,
            inputs=[
                input_img,
                auto_expand_chk,
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
                target_w,
                target_h,
            ],
            outputs=[output_img, mask],
        )

        send_btn.click(fn=None, _js="() => { mos_img2inpaint(); }")
        send_m_btn.click(fn=None, _js="() => { mos_img2inpaintupload(); }")

        cnet_send_btn.click(
            fn=None,
            inputs=[cnet_mode, cnet_id],
            _js="(m, i) => { mos_img2cnet(m, i); }",
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
            target_w,
            target_h,
            auto_expand_chk,
        ]:
            comp.do_not_save_to_config = True

    return [(mos_UI, "Mosaic", "sd-webui-mosaic-io")]


script_callbacks.on_ui_tabs(mos_ui)
