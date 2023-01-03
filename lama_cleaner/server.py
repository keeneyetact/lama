#!/usr/bin/env python3

import io
import json
import logging
import multiprocessing
import os
import random
import time
import imghdr
from pathlib import Path
from typing import Union
from PIL import Image

import cv2
import torch
import numpy as np
from loguru import logger

from lama_cleaner.interactive_seg import InteractiveSeg, Click
from lama_cleaner.model_manager import ModelManager
from lama_cleaner.schema import Config

try:
    torch._C._jit_override_can_fuse_on_cpu(False)
    torch._C._jit_override_can_fuse_on_gpu(False)
    torch._C._jit_set_texpr_fuser_enabled(False)
    torch._C._jit_set_nvfuser_enabled(False)
except:
    pass

from flask import Flask, request, send_file, cli, make_response

# Disable ability for Flask to display warning about using a development server in a production environment.
# https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356
cli.show_server_banner = lambda *_: None
from flask_cors import CORS

from lama_cleaner.helper import (
    load_img,
    numpy_to_bytes,
    resize_max_size,
)

NUM_THREADS = str(multiprocessing.cpu_count())

# fix libomp problem on windows https://github.com/Sanster/lama-cleaner/issues/56
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

os.environ["OMP_NUM_THREADS"] = NUM_THREADS
os.environ["OPENBLAS_NUM_THREADS"] = NUM_THREADS
os.environ["MKL_NUM_THREADS"] = NUM_THREADS
os.environ["VECLIB_MAXIMUM_THREADS"] = NUM_THREADS
os.environ["NUMEXPR_NUM_THREADS"] = NUM_THREADS
if os.environ.get("CACHE_DIR"):
    os.environ["TORCH_HOME"] = os.environ["CACHE_DIR"]

BUILD_DIR = os.environ.get("LAMA_CLEANER_BUILD_DIR", "app/build")


class NoFlaskwebgui(logging.Filter):
    def filter(self, record):
        return "flaskwebgui-keep-server-alive" not in record.getMessage()


logging.getLogger("werkzeug").addFilter(NoFlaskwebgui())

app = Flask(__name__, static_folder=os.path.join(BUILD_DIR, "static"))
app.config["JSON_AS_ASCII"] = False
CORS(app, expose_headers=["Content-Disposition"])
# MAX_BUFFER_SIZE = 50 * 1000 * 1000  # 50 MB
# async_mode 优先级: eventlet/gevent_uwsgi/gevent/threading
# only threading works on macOS
# socketio = SocketIO(app, max_http_buffer_size=MAX_BUFFER_SIZE, async_mode='threading')

model: ModelManager = None
interactive_seg_model: InteractiveSeg = None
device = None
input_image_path: str = None
is_disable_model_switch: bool = False
is_desktop: bool = False


def get_image_ext(img_bytes):
    w = imghdr.what("", img_bytes)
    if w is None:
        w = "jpeg"
    return w


def diffuser_callback(i, t, latents):
    pass
    # socketio.emit('diffusion_step', {'diffusion_step': step})


@app.route("/inpaint", methods=["POST"])
def process():
    input = request.files
    # RGB
    origin_image_bytes = input["image"].read()
    image, alpha_channel = load_img(origin_image_bytes)

    mask, _ = load_img(input["mask"].read(), gray=True)
    mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]

    if image.shape[:2] != mask.shape[:2]:
        return f"Mask shape{mask.shape[:2]} not queal to Image shape{image.shape[:2]}", 400

    original_shape = image.shape
    interpolation = cv2.INTER_CUBIC

    form = request.form
    size_limit: Union[int, str] = form.get("sizeLimit", "1080")
    if size_limit == "Original":
        size_limit = max(image.shape)
    else:
        size_limit = int(size_limit)

    if "paintByExampleImage" in input:
        paint_by_example_example_image, _ = load_img(input["paintByExampleImage"].read())
        paint_by_example_example_image = Image.fromarray(paint_by_example_example_image)
    else:
        paint_by_example_example_image = None

    config = Config(
        ldm_steps=form["ldmSteps"],
        ldm_sampler=form["ldmSampler"],
        hd_strategy=form["hdStrategy"],
        zits_wireframe=form["zitsWireframe"],
        hd_strategy_crop_margin=form["hdStrategyCropMargin"],
        hd_strategy_crop_trigger_size=form["hdStrategyCropTrigerSize"],
        hd_strategy_resize_limit=form["hdStrategyResizeLimit"],
        prompt=form["prompt"],
        negative_prompt=form["negativePrompt"],
        use_croper=form["useCroper"],
        croper_x=form["croperX"],
        croper_y=form["croperY"],
        croper_height=form["croperHeight"],
        croper_width=form["croperWidth"],
        sd_mask_blur=form["sdMaskBlur"],
        sd_strength=form["sdStrength"],
        sd_steps=form["sdSteps"],
        sd_guidance_scale=form["sdGuidanceScale"],
        sd_sampler=form["sdSampler"],
        sd_seed=form["sdSeed"],
        sd_match_histograms=form["sdMatchHistograms"],
        cv2_flag=form["cv2Flag"],
        cv2_radius=form['cv2Radius'],
        paint_by_example_steps=form["paintByExampleSteps"],
        paint_by_example_guidance_scale=form["paintByExampleGuidanceScale"],
        paint_by_example_mask_blur=form["paintByExampleMaskBlur"],
        paint_by_example_seed=form["paintByExampleSeed"],
        paint_by_example_match_histograms=form["paintByExampleMatchHistograms"],
        paint_by_example_example_image=paint_by_example_example_image,
    )

    if config.sd_seed == -1:
        config.sd_seed = random.randint(1, 999999999)
    if config.paint_by_example_seed == -1:
        config.paint_by_example_seed = random.randint(1, 999999999)

    logger.info(f"Origin image shape: {original_shape}")
    image = resize_max_size(image, size_limit=size_limit, interpolation=interpolation)
    logger.info(f"Resized image shape: {image.shape}")

    mask = resize_max_size(mask, size_limit=size_limit, interpolation=interpolation)

    start = time.time()
    try:
        res_np_img = model(image, mask, config)
    except RuntimeError as e:
        torch.cuda.empty_cache()
        if "CUDA out of memory. " in str(e):
            # NOTE: the string may change?
            return "CUDA out of memory", 500
        else:
            logger.exception(e)
            return "Internal Server Error", 500
    finally:
        logger.info(f"process time: {(time.time() - start) * 1000}ms")
        torch.cuda.empty_cache()

    if alpha_channel is not None:
        if alpha_channel.shape[:2] != res_np_img.shape[:2]:
            alpha_channel = cv2.resize(
                alpha_channel, dsize=(res_np_img.shape[1], res_np_img.shape[0])
            )
        res_np_img = np.concatenate(
            (res_np_img, alpha_channel[:, :, np.newaxis]), axis=-1
        )

    ext = get_image_ext(origin_image_bytes)

    response = make_response(
        send_file(
            io.BytesIO(numpy_to_bytes(res_np_img, ext)),
            mimetype=f"image/{ext}",
        )
    )
    response.headers["X-Seed"] = str(config.sd_seed)
    return response


@app.route("/interactive_seg", methods=["POST"])
def interactive_seg():
    input = request.files
    origin_image_bytes = input["image"].read()  # RGB
    image, _ = load_img(origin_image_bytes)
    if 'mask' in input:
        mask, _ = load_img(input["mask"].read(), gray=True)
    else:
        mask = None

    _clicks = json.loads(request.form["clicks"])
    clicks = []
    for i, click in enumerate(_clicks):
        clicks.append(Click(coords=(click[1], click[0]), indx=i, is_positive=click[2] == 1))

    start = time.time()
    new_mask = interactive_seg_model(image, clicks=clicks, prev_mask=mask)
    logger.info(f"interactive seg process time: {(time.time() - start) * 1000}ms")
    response = make_response(
        send_file(
            io.BytesIO(numpy_to_bytes(new_mask, 'png')),
            mimetype=f"image/png",
        )
    )
    return response


@app.route("/model")
def current_model():
    return model.name, 200


@app.route("/is_disable_model_switch")
def get_is_disable_model_switch():
    res = 'true' if is_disable_model_switch else 'false'
    return res, 200


@app.route("/model_downloaded/<name>")
def model_downloaded(name):
    return str(model.is_downloaded(name)), 200


@app.route("/is_desktop")
def get_is_desktop():
    return str(is_desktop), 200


@app.route("/model", methods=["POST"])
def switch_model():
    if is_disable_model_switch:
        return "Switch model is disabled", 400

    new_name = request.form.get("name")
    if new_name == model.name:
        return "Same model", 200

    try:
        model.switch(new_name)
    except NotImplementedError:
        return f"{new_name} not implemented", 403
    return f"ok, switch to {new_name}", 200


@app.route("/")
def index():
    return send_file(os.path.join(BUILD_DIR, "index.html"), cache_timeout=0)


@app.route("/inputimage")
def set_input_photo():
    if input_image_path:
        with open(input_image_path, "rb") as f:
            image_in_bytes = f.read()
        return send_file(
            input_image_path,
            as_attachment=True,
            attachment_filename=Path(input_image_path).name,
            mimetype=f"image/{get_image_ext(image_in_bytes)}",
        )
    else:
        return "No Input Image"


def main(args):
    global model
    global interactive_seg_model
    global device
    global input_image_path
    global is_disable_model_switch
    global is_desktop

    device = torch.device(args.device)
    input_image_path = args.input
    is_disable_model_switch = args.disable_model_switch
    is_desktop = args.gui
    if is_disable_model_switch:
        logger.info(f"Start with --disable-model-switch, model switch on frontend is disable")

    model = ModelManager(
        name=args.model,
        device=device,
        no_half=args.no_half,
        hf_access_token=args.hf_access_token,
        sd_disable_nsfw=args.sd_disable_nsfw,
        sd_cpu_textencoder=args.sd_cpu_textencoder,
        sd_run_local=args.sd_run_local,
        sd_enable_xformers=args.sd_enable_xformers,
        callback=diffuser_callback,
    )

    interactive_seg_model = InteractiveSeg()

    if args.gui:
        app_width, app_height = args.gui_size
        from flaskwebgui import FlaskUI

        ui = FlaskUI(
            app, width=app_width, height=app_height, host=args.host, port=args.port
        )
        ui.run()
    else:
        # TODO: socketio
        app.run(host=args.host, port=args.port, debug=args.debug)
