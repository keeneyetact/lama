import cv2
from loguru import logger

from lama_cleaner.helper import download_model
from lama_cleaner.plugins.base_plugin import BasePlugin


class RestoreFormerPlugin(BasePlugin):
    name = "RestoreFormer"

    def __init__(self, device, upscaler=None):
        super().__init__()
        from .gfpganer import MyGFPGANer

        url = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/RestoreFormer.pth"
        model_md5 = "eaeeff6c4a1caa1673977cb374e6f699"
        model_path = download_model(url, model_md5)
        logger.info(f"RestoreFormer model path: {model_path}")

        import facexlib

        if hasattr(facexlib.detection.retinaface, "device"):
            facexlib.detection.retinaface.device = device

        self.face_enhancer = MyGFPGANer(
            model_path=model_path,
            upscale=1,
            arch="RestoreFormer",
            channel_multiplier=2,
            device=device,
            bg_upsampler=upscaler.model if upscaler is not None else None,
        )

    def __call__(self, rgb_np_img, files, form):
        weight = 0.5
        bgr_np_img = cv2.cvtColor(rgb_np_img, cv2.COLOR_RGB2BGR)
        logger.info(f"RestoreFormer input shape: {bgr_np_img.shape}")
        _, _, bgr_output = self.face_enhancer.enhance(
            bgr_np_img,
            has_aligned=False,
            only_center_face=False,
            paste_back=True,
            weight=weight,
        )
        logger.info(f"RestoreFormer output shape: {bgr_output.shape}")
        return bgr_output

    def check_dep(self):
        try:
            import gfpgan
        except ImportError:
            return (
                "gfpgan is not installed, please install it first. pip install gfpgan"
            )
