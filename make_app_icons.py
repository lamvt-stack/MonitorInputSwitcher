#!/usr/bin/env python3
"""Application icons for Monitor Input Switcher.

  app.ico         full-colour tile (exe / shortcuts)
  tray-light.ico  light bezel  -> for DARK taskbars
  tray-dark.ico   dark bezel   -> for LIGHT taskbars

Concept: a monitor whose screen carries the "swap" arrows - i.e. one display, several inputs.
The screen always keeps the colour splash (teal -> indigo); only the bezel changes between
the light and dark tray variants, so the icon stays legible on either taskbar.

ICO files use classic 32-bit BMP images for 16..128 px and PNG for 256 px, the layout every
Windows resource compiler (rc.exe, windres) accepts."""
import io, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

N = 1024
SIZES_APP = [16, 20, 24, 32, 40, 48, 64, 128, 256]
SIZES_TRAY = [16, 20, 24, 32, 40, 48]          # tray icons never need more (100%..300% DPI)
CLEAR = (0, 0, 0, 0)


def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def gradient(size, c1, c2, angle=0.55):
    n = 256
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    t = np.clip((xs * (1 - angle) + ys * angle) / (n - 1), 0, 1)[..., None]
    a = np.array(c1[:3], np.float32); b = np.array(c2[:3], np.float32)
    arr = (a + (b - a) * t).astype(np.uint8)
    return Image.fromarray(arr, "RGB").resize(size, Image.BICUBIC).convert("RGBA")


def thick(d, pts, wd, fill):
    d.line(pts, fill=fill, width=wd, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse((p[0] - wd / 2, p[1] - wd / 2, p[0] + wd / 2, p[1] + wd / 2), fill=fill)


SCREEN_A, SCREEN_B = '#14C8C0', '#5B4CF0'      # teal -> indigo: the colour splash
LED = '#FF9F1C'


def monitor(bezel, small, scale=1.0, offset=(0, 0)):
    """Monitor glyph on a transparent 1024 canvas (bezel colour as given)."""
    bz = 96 if small else 66                                   # bezel thickness: bolder for tiny sizes
    body = (48, 118, 976, 764)
    scr = (body[0] + bz, body[1] + bz, body[2] - bz, body[3] - bz - (0 if small else 8))
    layer = Image.new("RGBA", (N, N), CLEAR)
    d = ImageDraw.Draw(layer)

    # stand + body (bezel colour)
    d.rounded_rectangle((424, 750, 600, 870), radius=20, fill=bezel)
    d.rounded_rectangle((286, 846, 738, 932), radius=43, fill=bezel)
    d.rounded_rectangle(body, radius=112, fill=bezel)

    # screen with the colour gradient
    sw, sh = scr[2] - scr[0], scr[3] - scr[1]
    grad = gradient((sw, sh), hexc(SCREEN_A), hexc(SCREEN_B))
    m = Image.new("L", (sw * 2, sh * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, sw * 2 - 1, sh * 2 - 1), radius=(64 if small else 72) * 2, fill=255)
    m = m.resize((sw, sh), Image.LANCZOS)
    grad.putalpha(m)
    # soft sheen across the upper-left of the screen
    sheen = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(sheen).polygon([(0, 0), (int(sw * 0.62), 0), (0, int(sh * 0.78))], fill=46 if not small else 30)
    sheen = ImageChops.multiply(sheen, m)
    white = Image.new("RGBA", (sw, sh), (255, 255, 255, 0)); white.putalpha(sheen)
    grad = Image.alpha_composite(grad, white)
    layer.alpha_composite(grad, (scr[0], scr[1]))

    # "swap" arrows: one display, many inputs
    cx, cy = (scr[0] + scr[2]) // 2, (scr[1] + scr[3]) // 2
    wd = 76 if small else 58                                   # stroke
    half = 262 if not small else 250
    gap = 92 if not small else 104
    hh = 108 if not small else 118                             # arrow-head half height
    W = (255, 255, 255, 255)
    ad = ImageDraw.Draw(layer)
    y1, y2 = cy - gap // 2 - 4, cy + gap // 2 + 4
    thick(ad, [(cx - half, y1), (cx + half - 70, y1)], wd, W)
    ad.polygon([(cx + half - 118, y1 - hh), (cx + half + 36, y1), (cx + half - 118, y1 + hh)], fill=W)
    thick(ad, [(cx + half, y2), (cx - half + 70, y2)], wd, W)
    ad.polygon([(cx - half + 118, y2 - hh), (cx - half - 36, y2), (cx - half + 118, y2 + hh)], fill=W)

    if not small:                                              # power LED = second splash of colour
        ad.ellipse((864 - 17, 735 - 17, 864 + 17, 735 + 17), fill=hexc(LED))

    if scale != 1.0 or offset != (0, 0):
        s = int(N * scale)
        layer = layer.resize((s, s), Image.LANCZOS)
        out = Image.new("RGBA", (N, N), CLEAR)
        out.alpha_composite(layer, ((N - s) // 2 + offset[0], (N - s) // 2 + offset[1]))
        layer = out
    return layer


def tile(small=False):
    """Full-colour application icon: squircle tile + monitor glyph with soft shadow."""
    bg = gradient((N, N), hexc('#7C6CFF'), hexc('#241A7A'), angle=0.6)
    big = Image.new("L", (N * 2, N * 2), 0)
    ImageDraw.Draw(big).rounded_rectangle((56, 56, N * 2 - 56, N * 2 - 56), radius=470, fill=255)
    mask = big.resize((N, N), Image.LANCZOS)
    bg.putalpha(mask)
    # gloss
    g = np.clip(1.0 - np.arange(N, dtype=np.float32)[:, None] / 600.0, 0, 1) * np.ones((1, N), np.float32) * 60
    gl = ImageChops.multiply(Image.fromarray(g.astype(np.uint8), "L"), mask)
    gloss = Image.new("RGBA", (N, N), (255, 255, 255, 0)); gloss.putalpha(gl)
    img = Image.alpha_composite(bg, gloss)
    glyph = monitor(hexc('#FFFFFF'), small, scale=0.66, offset=(0, 6))
    sh = Image.new("RGBA", (N, N), (10, 5, 60, 255)); sh.putalpha(glyph.getchannel("A").point(lambda v: int(v * 0.35)))
    sh = ImageChops.offset(sh.filter(ImageFilter.GaussianBlur(18)), 0, 18)
    img = Image.alpha_composite(img, sh)
    return Image.alpha_composite(img, glyph)


def variants(kind, size):
    small = size <= 32
    if kind == "app":
        return tile(small)
    bezel = hexc('#FFFFFF') if kind == "light" else hexc('#1B2433')
    return monitor(bezel, small)


# --------------------------------------------------------------------------------- ICO writing
def bmp_image(im):
    s = im.width
    arr = np.array(im.convert("RGBA"))                            # straight alpha, RGBA
    bgra = arr[::-1][:, :, [2, 1, 0, 3]].tobytes()                # bottom-up BGRA
    mask = bytes(((s + 31) // 32) * 4 * s)                        # AND mask (unused with alpha)
    hdr = struct.pack("<IiiHHIIiiII", 40, s, s * 2, 1, 32, 0, len(bgra) + len(mask), 0, 0, 0, 0)
    return hdr + bgra + mask


def png_image(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return b.getvalue()


def write_ico(path, kind):
    masters = {}
    frames = []
    for s in (SIZES_APP if kind == "app" else SIZES_TRAY):
        key = "small" if s <= 32 else "big"
        if key not in masters:
            masters[key] = variants(kind, s)
        im = masters[key].resize((s, s), Image.LANCZOS)
        frames.append((s, png_image(im) if s >= 64 else bmp_image(im)))   # BMP up to 48 px, PNG above (compact)
    head = struct.pack("<HHH", 0, 1, len(frames))
    off = 6 + 16 * len(frames)
    ents, blobs = b"", b""
    for s, data in frames:
        dim = 0 if s >= 256 else s
        ents += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), off)
        blobs += data; off += len(data)
    with open(path, "wb") as f:
        f.write(head + ents + blobs)
    return masters


def preview(outdir):
    font = ImageFont.load_default(size=14)
    rows = [("app", "app.ico"), ("light", "tray-light.ico  (for dark taskbar)"), ("dark", "tray-dark.ico  (for light taskbar)")]
    shown = [128, 48, 32, 24, 20, 16]
    W_, H_ = 1360, 3 * 200 + 40
    sheet = Image.new("RGB", (W_, H_), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    # left half light background, right half dark background
    d.rectangle((0, 0, W_ // 2 - 1, H_), fill=(243, 245, 249))
    d.rectangle((W_ // 2, 0, W_, H_), fill=(32, 34, 40))
    masters = {k: {} for k, _ in rows}
    for k, _ in rows:
        masters[k]["small"] = variants(k, 16); masters[k]["big"] = variants(k, 64)
    for r, (k, label) in enumerate(rows):
        for half in (0, 1):
            x = 20 + half * (W_ // 2)
            y0 = 30 + r * 200
            d.text((x, y0 - 22), label, fill=(60, 64, 75) if half == 0 else (210, 214, 224), font=font)
            cx = x
            for s in shown:
                im = masters[k]["small" if s <= 32 else "big"].resize((s, s), Image.LANCZOS)
                sheet.paste(im, (cx, y0 + (150 - s) // 2 if s > 48 else y0 + 40), im)
                cx += s + 22 if s >= 48 else s + 16
            # magnified 16/24 px (nearest) to inspect pixels
            for s, mag in ((16, 6), (24, 4)):
                im = masters[k]["small"].resize((s, s), Image.LANCZOS).resize((s * mag, s * mag), Image.NEAREST)
                sheet.paste(im, (cx, y0 + 10), im); cx += s * mag + 12
    sheet.save(os.path.join(outdir, "app-icons-preview.png"))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/appicons"
    os.makedirs(out, exist_ok=True)
    for name, kind in (("app", "app"), ("tray-light", "light"), ("tray-dark", "dark")):
        m = write_ico(os.path.join(out, f"{name}.ico"), kind)
        m.setdefault("big", variants(kind, 256))
        m["big"].resize((256, 256), Image.LANCZOS).save(os.path.join(out, f"{name}-256.png"))
        print("ok", name)
    preview(out)
