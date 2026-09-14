"""Pixel Encoding - Steganography using image channels."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

HELP = """USAGE:
  key pix [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode text into image
  -d, --decode  Decode text from image
OPTIONS:
  -t, --text <text>         Text to encode
  -f, --file <path>         Input image file (for decode)
  -o, --output <path>       Output image file
  -c, --channel <channel>   RGB channel: 0=R, 1=G, 2=B (default: 0)
  -ii, --inputImage <path>  Input image for decoding
EXAMPLES:
  key pix -e -t "secret" -o output.png
  key pix -d -ii output.png
"""


class Cipher(BaseCipher):
    """Pixel encoding steganography cipher."""

    name = "Pixel Encoding"
    command = "pix"
    help_menu = HELP

    def encode(self, args):
        text = getattr(args, "text", None)
        output = getattr(args, "output", None)
        channel = getattr(args, "channel", None) or 0
        if not text:
            return CipherResult("Please provide -t <text>", False)
        try:
            from PIL import Image

            pixels = [ord(c) for c in text]
            size = len(pixels)
            width = int(size**0.5) + 1
            height = (size // width) + 1
            img = Image.new("RGB", (width, height))
            for i, pixel_val in enumerate(pixels):
                x = i % width
                y = i // width
                r, g, b = img.getpixel((x, y))
                if channel == 0:
                    r = pixel_val
                elif channel == 1:
                    g = pixel_val
                else:
                    b = pixel_val
                img.putpixel((x, y), (r, g, b))
            if output:
                img.save(output)
                return CipherResult(f"Image saved to {output}", True)
            return CipherResult("Provide -o <output> to save image", False)
        except ImportError:
            return CipherResult("Install Pillow: pip install Pillow", False)
        except Exception as e:
            return CipherResult(f"Encoding failed: {e}", False)

    def decode(self, args):
        input_img = getattr(args, "inputImage", None)
        channel = getattr(args, "channel", None) or 0
        if not input_img:
            return CipherResult("Provide -ii <inputImage> to decode", False)
        try:
            from PIL import Image

            img = Image.open(input_img)
            width, height = img.size
            pixels = []
            for y in range(height):
                for x in range(width):
                    r, g, b = img.getpixel((x, y))
                    if channel == 0:
                        val = r
                    elif channel == 1:
                        val = g
                    else:
                        val = b
                    if val > 0:
                        pixels.append(val)
            return CipherResult("".join(chr(p) for p in pixels), True)
        except ImportError:
            return CipherResult("Install Pillow: pip install Pillow", False)
        except Exception as e:
            return CipherResult(f"Decoding failed: {e}", False)
