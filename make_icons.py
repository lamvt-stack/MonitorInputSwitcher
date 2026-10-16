#!/usr/bin/env python3
"""Procedural icon set for Monitor Input Switcher buttons.
Draws each icon at 1024px (supersampled), then writes PNG-compressed multi-size .ico
files (32, 48, 64, 128, 256) plus PNG previews and a contact sheet."""
import io, math, os, struct, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

N = 1024
SIZES = [32, 48, 64, 128, 256]
W = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)


def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ---------------------------------------------------------------- drawing helpers
def rr(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)


def rrt(d, box, r, fill):                      # rounded on top only
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=r, fill=fill)
    d.rectangle((x0, (y0 + y1) // 2, x1, y1), fill=fill)


def circ(d, cx, cy, r, fill):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def thick(d, pts, wd, fill):                   # polyline with round caps/joints
    d.line(pts, fill=fill, width=wd, joint="curve")
    for p in pts:
        circ(d, p[0], p[1], wd / 2 - 0.5, fill)


def soft_poly(d, pts, fill, grow=24):          # polygon with softened corners
    d.polygon(pts, fill=fill)
    d.line(list(pts) + [pts[0]], fill=fill, width=grow, joint="curve")
    for p in pts:
        circ(d, p[0], p[1], grow / 2 - 0.5, fill)


def scale_pts(pts, k, c=(512, 512)):
    return [(c[0] + (x - c[0]) * k, c[1] + (y - c[1]) * k) for x, y in pts]


# ---------------------------------------------------------------- glyphs
# each glyph(w, a, t, A): w = white layer, a = accent layer (above w), t = top layer (above a)
def g_home(w, a, t, A):
    rr(w, (290, 470, 734, 810), 56, W)
    w.polygon([(512, 240), (232, 520), (792, 520)], fill=W)
    thick(w, [(150, 520), (512, 215), (874, 520)], 96, W)
    rr(w, (632, 232, 714, 372), 16, W)
    rrt(w, (446, 590, 578, 830), 44, CLEAR)
    rrt(a, (446, 590, 578, 810), 44, A)
    circ(a, 556, 702, 9, W)


def g_work(w, a, t, A):
    rr(w, (375, 230, 649, 430), 64, W)
    rr(w, (431, 288, 593, 430), 30, CLEAR)
    rr(w, (180, 340, 844, 800), 76, W)
    a.rectangle((180, 530, 844, 588), fill=A)
    rr(a, (448, 498, 576, 620), 24, W)
    rr(a, (480, 530, 544, 588), 12, A)


def g_business(w, a, t, A):
    rr(w, (280, 200, 640, 810), 36, W)
    rr(w, (668, 430, 808, 810), 30, W)
    rr(w, (190, 790, 834, 842), 26, W)
    cols, rows = (322, 426, 530), (262, 366, 470, 574)
    for cx in cols:
        for ry in rows:
            rr(w, (cx, ry, cx + 68, ry + 68), 14, CLEAR)
    for cx, ry in ((426, 366), (530, 470), (322, 574)):
        rr(a, (cx, ry, cx + 68, ry + 68), 14, A)
    rrt(w, (426, 690, 530, 800), 14, CLEAR)
    for ry in (486, 586, 686):
        rr(w, (692, ry, 784, ry + 56), 12, CLEAR)
    rr(a, (692, 586, 784, 642), 12, A)


def g_network(w, a, t, A):
    nodes = [(240, 270), (784, 270), (240, 754), (784, 754)]
    for n in nodes:
        thick(w, [(512, 512), n], 42, W)
    for n in nodes:
        circ(w, n[0], n[1], 84, W)
    circ(w, 512, 512, 140, W)
    circ(a, 512, 512, 92, A)


def g_internet(w, a, t, A):
    R = 318
    w.ellipse((512 - R, 512 - R, 512 + R, 512 + R), outline=W, width=54)
    for dy in (-168, 168):
        hc = int(math.sqrt(R * R - dy * dy)) - 30
        thick(w, [(512 - hc, 512 + dy), (512 + hc, 512 + dy)], 42, W)
    w.rectangle((512 - R + 20, 512 - 21, 512 + R - 20, 512 + 21), fill=W)
    a.ellipse((512 - 142, 512 - R + 14, 512 + 142, 512 + R - 14), outline=A, width=46)


def g_gaming(w, a, t, A):
    rr(w, (170, 340, 854, 680), 160, W)
    rr(w, (180, 470, 440, 810), 130, W)
    rr(w, (584, 470, 844, 810), 130, W)
    # d-pad cutout
    rr(w, (252, 480, 388, 540), 22, CLEAR)
    rr(w, (290, 442, 350, 578), 22, CLEAR)
    cols = [hexc('#FF5C8A'), hexc('#FFD43B'), hexc('#4ADE80'), hexc('#38BDF8')]
    for (x, y), c in zip([(704, 440), (766, 504), (704, 568), (642, 504)], cols):
        circ(a, x, y, 36, c)
    rr(w, (440, 470, 484, 500), 12, CLEAR)
    rr(w, (540, 470, 584, 500), 12, CLEAR)


def g_media(w, a, t, A):
    rr(w, (170, 250, 854, 730), 100, W)
    tri = [(446, 392), (446, 590), (622, 491)]
    soft_poly(a, tri, A, grow=44)
    rr(w, (470, 730, 554, 790), 0, W)
    rr(w, (360, 770, 664, 826), 28, W)


def g_music(w, a, t, A):
    w.rectangle((412, 330, 460, 712), fill=W)
    w.rectangle((668, 268, 716, 652), fill=W)
    w.ellipse((282, 640, 462, 790), fill=W)
    w.ellipse((538, 580, 718, 730), fill=W)
    a.polygon([(412, 322), (716, 252), (716, 360), (412, 430)], fill=A)


def g_creative(w, a, t, A):
    w.ellipse((170, 240, 854, 790), fill=W)
    circ(w, 652, 652, 68, CLEAR)
    for (x, y), c in zip([(330, 470), (480, 352), (660, 352), (778, 500)],
                         ['#FF4D4D', '#FFC53D', '#2ED47A', '#3B82F6']):
        circ(a, x, y, 58, hexc(c))


def g_photo(w, a, t, A):
    rr(w, (170, 230, 854, 794), 84, W)
    rr(a, (236, 296, 788, 728), 38, hexc('#6EC6FF'))
    circ(a, 640, 424, 58, A)
    t.polygon([(236, 728), (236, 650), (372, 488), (496, 628), (590, 540), (788, 714), (788, 728)], fill=W)
    rr(t, (170, 700, 854, 794), 0, W)
    rr(t, (170, 700, 854, 794), 84, W)


def g_developer(w, a, t, A):
    thick(w, [(392, 318), (222, 512), (392, 706)], 86, W)
    thick(w, [(632, 318), (802, 512), (632, 706)], 86, W)
    thick(a, [(574, 284), (450, 740)], 66, A)


def g_videocall(w, a, t, A):
    rr(w, (170, 320, 642, 704), 88, W)
    soft_poly(w, [(666, 478), (846, 360), (846, 670), (666, 550)], W, grow=44)
    circ(a, 296, 438, 34, A)


def g_documents(w, a, t, A):
    rr(w, (250, 190, 774, 834), 70, W)
    w.polygon([(604, 180), (784, 180), (784, 360)], fill=CLEAR)
    a.polygon([(604, 190), (604, 360), (774, 360)], fill=A)
    rr(w, (336, 450, 688, 494), 22, CLEAR)
    rr(w, (336, 550, 688, 594), 22, CLEAR)
    rr(w, (336, 650, 560, 694), 22, CLEAR)


def g_finance(w, a, t, A):
    for x0, y0 in ((226, 610), (414, 500), (602, 390)):
        rr(w, (x0, y0, x0 + 128, 810), 28, W)
    thick(a, [(210, 462), (396, 330), (516, 420), (736, 232)], 50, A)
    a.polygon([(808, 268), (716, 160), (834, 150)], fill=A)


def g_education(w, a, t, A):
    w.polygon([(300, 500), (512, 612), (724, 500), (724, 662), (512, 774), (300, 662)], fill=(255, 255, 255, 232))
    soft_poly(w, [(512, 236), (872, 418), (512, 602), (152, 418)], W, grow=30)
    thick(a, [(836, 446), (836, 640)], 28, A)
    circ(a, 836, 672, 44, A)


def g_server(w, a, t, A):
    for y in (230, 420, 610):
        rr(w, (220, y, 804, y + 162), 42, W)
        circ(a, 316, y + 81, 26, A)
        circ(a, 394, y + 81, 26, hexc('#FFD43B'))
        rr(w, (480, y + 62, 726, y + 100), 19, CLEAR)


def g_cloud(w, a, t, A):
    circ(w, 340, 610, 112, W)
    circ(w, 500, 480, 172, W)
    circ(w, 690, 600, 122, W)
    w.rectangle((340, 600, 690, 722), fill=W)
    soft_poly(a, [(512, 440), (620, 548), (404, 548)], A, grow=26)
    a.rectangle((478, 540, 546, 668), fill=A)


def g_laptop(w, a, t, A):
    rr(w, (250, 250, 774, 640), 56, W)
    rr(a, (302, 302, 722, 588), 26, A)
    rr(w, (130, 676, 894, 760), 42, W)
    rr(w, (430, 676, 594, 706), 16, CLEAR)


def g_desktop(w, a, t, A):
    rr(w, (296, 180, 728, 844), 64, W)
    rr(w, (366, 266, 658, 308), 18, CLEAR)
    rr(w, (366, 346, 658, 388), 18, CLEAR)
    circ(a, 512, 664, 82, A)
    circ(a, 512, 664, 42, W)
    rr(w, (366, 466, 658, 482), 8, CLEAR)
    rr(w, (366, 506, 658, 522), 8, CLEAR)


def g_security(w, a, t, A):
    pts = [(512, 180), (820, 290), (820, 510), (770, 650), (664, 766), (512, 850),
           (360, 766), (254, 650), (204, 510), (204, 290)]
    soft_poly(w, scale_pts(pts, 0.92), W, grow=64)
    thick(a, [(372, 512), (478, 618), (664, 400)], 74, A)


def g_streaming(w, a, t, A):
    circ(w, 512, 512, 122, W)
    for r in (230, 340):
        w.arc((512 - r, 512 - r, 512 + r, 512 + r), -48, 48, fill=W, width=54)
        w.arc((512 - r, 512 - r, 512 + r, 512 + r), 132, 228, fill=W, width=54)
        for ang in (-48, 48, 132, 228):
            x = 512 + (r - 27) * math.cos(math.radians(ang))
            y = 512 + (r - 27) * math.sin(math.radians(ang))
            circ(w, x, y, 27, W)
    circ(a, 512, 512, 76, A)


def g_reading(w, a, t, A):
    left = [(166, 310), (496, 366), (496, 806), (166, 752)]
    right = [(858, 310), (528, 366), (528, 806), (858, 752)]
    soft_poly(w, left, W, grow=40)
    soft_poly(w, right, W, grow=40)
    a.polygon([(640, 340), (736, 324), (736, 540), (688, 498), (640, 548)], fill=A)


ICONS = [
    # name,        label,        gradient top-left, gradient bottom-right, accent,    glyph
    ("home",       "Home",       '#FFB36B', '#F25C2A', '#12A4B6', g_home),
    ("work",       "Work",       '#6C9BFF', '#1E3A8A', '#FFB020', g_work),
    ("business",   "Business",   '#8B93FF', '#4338CA', '#FFD166', g_business),
    ("network",    "Network",    '#34D3C0', '#0E7C86', '#FFC83D', g_network),
    ("internet",   "Internet",   '#43C6FF', '#0B6FB8', '#FFD54A', g_internet),
    ("gaming",     "Gaming",     '#B18CFF', '#5B21B6', '#FF5C8A', g_gaming),
    ("media",      "Media",      '#FF8A8A', '#C62828', '#FFA62B', g_media),
    ("music",      "Music",      '#FF7BD5', '#A21CAF', '#FFE066', g_music),
    ("creative",   "Creative",   '#FFC15E', '#E8590C', '#FFFFFF', g_creative),
    ("photo",      "Photo",      '#FFD36B', '#E8890C', '#FFD43B', g_photo),
    ("developer",  "Developer",  '#475569', '#0B1220', '#4ADE80', g_developer),
    ("video-call", "Video Call", '#4ADE9C', '#0A7A55', '#FF4D4D', g_videocall),
    ("documents",  "Documents",  '#74D0FF', '#1E6FE0', '#FFB020', g_documents),
    ("finance",    "Finance",    '#47D17A', '#117A3D', '#FFD60A', g_finance),
    ("education",  "Education",  '#FF9A8A', '#D32F2F', '#FFD54A', g_education),
    ("server",     "Server",     '#8294AE', '#2F3E54', '#4ADE80', g_server),
    ("cloud",      "Cloud",      '#6EC8FF', '#2B6CD6', '#FF7A00', g_cloud),
    ("laptop",     "Laptop",     '#7FA8FF', '#3347C9', '#FFD166', g_laptop),
    ("desktop",    "Desktop PC", '#FFA07A', '#D9480F', '#4ADE80', g_desktop),
    ("security",   "Security",   '#5B8CFF', '#1B2F8A', '#22C55E', g_security),
    ("streaming",  "Streaming",  '#F77FBE', '#BE185D', '#FF2D55', g_streaming),
    ("reading",    "Reading",    '#A3E635', '#4D7C0F', '#FF5252', g_reading),
]


# ---------------------------------------------------------------- compositing
def gradient(c1, c2):
    n = 256
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    t = np.clip((xs * 0.42 + ys * 0.58) / (n - 1), 0, 1)[..., None]
    a = np.array(c1[:3], np.float32); b = np.array(c2[:3], np.float32)
    arr = (a + (b - a) * t).astype(np.uint8)
    return Image.fromarray(arr, "RGB").resize((N, N), Image.BICUBIC).convert("RGBA")


def squircle_mask():
    big = Image.new("L", (N * 2, N * 2), 0)
    ImageDraw.Draw(big).rounded_rectangle((56, 56, N * 2 - 56, N * 2 - 56), radius=470, fill=255)
    return big.resize((N, N), Image.LANCZOS)


MASK = squircle_mask()


def gloss_layer():
    g = np.zeros((N, N), np.float32)
    ys = np.arange(N, dtype=np.float32)[:, None]
    g[:] = np.clip(1.0 - ys / 600.0, 0, 1) * 64
    gl = Image.fromarray(g.astype(np.uint8), "L")
    gl = ImageChops.multiply(gl, MASK)
    out = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    out.putalpha(gl)
    return out


GLOSS = gloss_layer()


def edge_layer():
    # subtle light inner rim + darker bottom rim for a "tile" feel
    rim = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    big = Image.new("RGBA", (N * 2, N * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((56, 56, N * 2 - 56, N * 2 - 56), radius=470, outline=(255, 255, 255, 70), width=8)
    rim = big.resize((N, N), Image.LANCZOS)
    return rim


RIM = edge_layer()


def render(c1, c2, accent, glyph):
    img = gradient(hexc(c1), hexc(c2))
    img.putalpha(MASK)
    img = Image.alpha_composite(img, GLOSS)
    img = Image.alpha_composite(img, RIM)

    lw = Image.new("RGBA", (N, N), CLEAR)
    la = Image.new("RGBA", (N, N), CLEAR)
    lt = Image.new("RGBA", (N, N), CLEAR)
    glyph(ImageDraw.Draw(lw), ImageDraw.Draw(la), ImageDraw.Draw(lt), hexc(accent))

    alpha = ImageChops.lighter(ImageChops.lighter(lw.getchannel("A"), la.getchannel("A")), lt.getchannel("A"))
    shadow = Image.new("RGBA", (N, N), (0, 0, 0, 255))
    shadow.putalpha(alpha.point(lambda v: int(v * 0.30)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    shadow = ImageChops.offset(shadow, 0, 16)
    img = Image.alpha_composite(img, shadow)
    for layer in (lw, la, lt):
        img = Image.alpha_composite(img, layer)
    return img


# ---------------------------------------------------------------- output
def png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def write_ico(path, master):
    frames = []
    for s in SIZES:
        im = master.resize((s, s), Image.LANCZOS)
        if s <= 48:
            im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=45, threshold=0))
        frames.append((s, png_bytes(im)))
    head = struct.pack("<HHH", 0, 1, len(frames))
    off = 6 + 16 * len(frames)
    entries, blobs = b"", b""
    for s, data in frames:
        dim = 0 if s >= 256 else s
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), off)
        blobs += data
        off += len(data)
    with open(path, "wb") as f:
        f.write(head + entries + blobs)


def contact_sheet(masters, path, cols=6, tile=176, pad=26, dark=False):
    rows = math.ceil(len(masters) / cols)
    font = ImageFont.load_default(size=15)
    bg = (24, 26, 32) if dark else (243, 245, 249)
    fg = (230, 232, 238) if dark else (50, 55, 65)
    sheet = Image.new("RGBA", (cols * (tile + pad) + pad, rows * (tile + pad + 26) + pad), bg + (255,))
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(masters):
        r, c = divmod(i, cols)
        x = pad + c * (tile + pad)
        y = pad + r * (tile + pad + 26)
        sheet.alpha_composite(im.resize((tile, tile), Image.LANCZOS), (x, y))
        tw = d.textlength(label, font=font)
        d.text((x + (tile - tw) / 2, y + tile + 6), label, fill=fg, font=font)
    sheet.convert("RGB").save(path)


def size_strip(masters, path):
    # shows every ICO size side by side on both light and dark, to judge legibility at 32px
    font = ImageFont.load_default(size=13)
    pad = 14
    rowh = 270
    sheet = Image.new("RGB", (len(masters) * 0 + 1400, 330), (243, 245, 249))
    d = ImageDraw.Draw(sheet)
    x = pad
    for label, im in masters[:6]:
        y = pad
        for s in (256, 128, 64, 48, 32):
            sheet.paste(im.resize((s, s), Image.LANCZOS), (x, y), im.resize((s, s), Image.LANCZOS))
            y += s + 6 if s > 64 else 0
        x += 0
    sheet.save(path)


def write_header(masters_by_name, path, px=128):
    """C header with the 128px PNG of every icon, embedded in the exe (see EmbIcon in the app)."""
    out = ["// Generated by make_icons.py - do not edit. 128px PNG images of the built-in icon set.",
           "#pragma once", "",
           "struct EmbIcon { const wchar_t* id; const wchar_t* title; const unsigned char* data; unsigned size; };", ""]
    for i, (name, label, m) in enumerate(masters_by_name):
        data = png_bytes(m.resize((px, px), Image.LANCZOS))
        out.append(f"// {name} ({len(data)} bytes)")
        out.append(f"static const unsigned char kEmbData{i}[] = {{")
        for k in range(0, len(data), 24):
            out.append("    " + ",".join(f"0x{b:02X}" for b in data[k:k + 24]) + ",")
        out.append("};")
    out.append("")
    out.append("static const EmbIcon kEmb[] = {")
    for i, (name, label, m) in enumerate(masters_by_name):
        out.append(f'    {{ L"{name}", L"{label}", kEmbData{i}, (unsigned)sizeof(kEmbData{i}) }},')
    out.append("};")
    out.append("static const int NEMB = (int)(sizeof(kEmb) / sizeof(kEmb[0]));")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def main(outdir, header=None):
    ico_dir = os.path.join(outdir, "ico")
    png_dir = os.path.join(outdir, "png")
    os.makedirs(ico_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    masters = []
    named = []
    for name, label, c1, c2, acc, fn in ICONS:
        m = render(c1, c2, acc, fn)
        masters.append((label, m))
        named.append((name, label, m))
        write_ico(os.path.join(ico_dir, f"{name}.ico"), m)
        m.resize((256, 256), Image.LANCZOS).save(os.path.join(png_dir, f"{name}-256.png"))
        print("ok", name)
    contact_sheet(masters, os.path.join(outdir, "preview.png"))
    contact_sheet(masters, os.path.join(outdir, "preview-dark.png"), dark=True)
    if header:
        write_header(named, header)
    return masters


if __name__ == "__main__":
    # usage: make_icons.py [outdir] [path/to/mis_icons.h]
    main(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/icons/out",
         sys.argv[2] if len(sys.argv) > 2 else None)
