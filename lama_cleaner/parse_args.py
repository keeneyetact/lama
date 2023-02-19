import os
import imghdr
import argparse
from pathlib import Path

from loguru import logger

from lama_cleaner.const import (
    AVAILABLE_MODELS,
    NO_HALF_HELP,
    CPU_OFFLOAD_HELP,
    DISABLE_NSFW_HELP,
    SD_CPU_TEXTENCODER_HELP,
    LOCAL_FILES_ONLY_HELP,
    AVAILABLE_DEVICES,
    ENABLE_XFORMERS_HELP,
    MODEL_DIR_HELP,
    OUTPUT_DIR_HELP,
    INPUT_HELP,
    GUI_HELP,
    DEFAULT_DEVICE,
    NO_GUI_AUTO_CLOSE_HELP,
    DEFAULT_MODEL_DIR,
    DEFAULT_MODEL,
    MPS_SUPPORT_MODELS,
)
from lama_cleaner.runtime import dump_environment_info


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)

    parser.add_argument(
        "--config-installer",
        action="store_true",
        help="Open config web page, mainly for windows installer",
    )
    parser.add_argument(
        "--load-installer-config",
        action="store_true",
        help="Load all cmd args from installer config file",
    )
    parser.add_argument(
        "--installer-config", default=None, help="Config file for windows installer"
    )

    parser.add_argument("--model", default=DEFAULT_MODEL, choices=AVAILABLE_MODELS)
    parser.add_argument("--no-half", action="store_true", help=NO_HALF_HELP)
    parser.add_argument("--cpu-offload", action="store_true", help=CPU_OFFLOAD_HELP)
    parser.add_argument("--disable-nsfw", action="store_true", help=DISABLE_NSFW_HELP)
    parser.add_argument(
        "--sd-cpu-textencoder", action="store_true", help=SD_CPU_TEXTENCODER_HELP
    )
    parser.add_argument(
        "--local-files-only", action="store_true", help=LOCAL_FILES_ONLY_HELP
    )
    parser.add_argument(
        "--enable-xformers", action="store_true", help=ENABLE_XFORMERS_HELP
    )
    parser.add_argument(
        "--device", default=DEFAULT_DEVICE, type=str, choices=AVAILABLE_DEVICES
    )
    parser.add_argument("--gui", action="store_true", help=GUI_HELP)
    parser.add_argument(
        "--no-gui-auto-close", action="store_true", help=NO_GUI_AUTO_CLOSE_HELP
    )
    parser.add_argument(
        "--gui-size",
        default=[1600, 1000],
        nargs=2,
        type=int,
        help="Set window size for GUI",
    )
    parser.add_argument("--input", type=str, default=None, help=INPUT_HELP)
    parser.add_argument("--output-dir", type=str, default=None, help=OUTPUT_DIR_HELP)
    parser.add_argument(
        "--model-dir", type=str, default=DEFAULT_MODEL_DIR, help=MODEL_DIR_HELP
    )
    parser.add_argument(
        "--disable-model-switch",
        action="store_true",
        help="Disable model switch in frontend",
    )
    parser.add_argument("--debug", action="store_true")

    # useless args
    parser.add_argument(
        "--hf_access_token",
        default="",
        help="SD model no more need token: https://github.com/huggingface/diffusers/issues/1447",
    )
    parser.add_argument(
        "--sd-disable-nsfw",
        action="store_true",
        help="Disable Stable Diffusion NSFW checker",
    )
    parser.add_argument(
        "--sd-run-local",
        action="store_true",
        help="SD model no more need token, use --local-files-only to set not connect to huggingface server",
    )
    parser.add_argument(
        "--sd-enable-xformers",
        action="store_true",
        help="Enable xFormers optimizations. Requires that xformers package has been installed. See: https://github.com/facebookresearch/xformers",
    )

    args = parser.parse_args()

    # collect system info to help debug
    dump_environment_info()

    if args.config_installer:
        if args.installer_config is None:
            parser.error(
                f"args.config_installer==True, must set args.installer_config to store config file"
            )
        from lama_cleaner.web_config import main

        logger.info(f"Launching installer web config page")
        main(args.installer_config)
        exit()

    if args.load_installer_config:
        from lama_cleaner.web_config import load_config

        if args.installer_config and not os.path.exists(args.installer_config):
            parser.error(f"args.installer_config={args.installer_config} not exists")

        logger.info(f"Loading installer config from {args.installer_config}")
        _args = load_config(args.installer_config)
        for k, v in vars(_args).items():
            if k in vars(args):
                setattr(args, k, v)

    if args.device == "cuda":
        import torch

        if torch.cuda.is_available() is False:
            parser.error(
                "torch.cuda.is_available() is False, please use --device cpu or check your pytorch installation"
            )

    if args.model_dir and args.model_dir is not None:
        if os.path.isfile(args.model_dir):
            parser.error(f"invalid --model-dir: {args.model_dir} is a file")

        if not os.path.exists(args.model_dir):
            logger.info(f"Create model cache directory: {args.model_dir}")
            Path(args.model_dir).mkdir(exist_ok=True, parents=True)

        os.environ["XDG_CACHE_HOME"] = args.model_dir

    if args.input and args.input is not None:
        if not os.path.exists(args.input):
            parser.error(f"invalid --input: {args.input} not exists")
        if os.path.isfile(args.input):
            if imghdr.what(args.input) is None:
                parser.error(f"invalid --input: {args.input} is not a valid image file")
        else:
            if args.output_dir is None:
                parser.error(
                    f"invalid --input: {args.input} is a directory, --output-dir is required"
                )

    if args.output_dir is not None:
        output_dir = Path(args.output_dir)
        if not output_dir.exists():
            logger.info(f"Creating output directory: {output_dir}")
            output_dir.mkdir(parents=True)
        else:
            if not output_dir.is_dir():
                parser.error(f"invalid --output-dir: {output_dir} is not a directory")

    return args
