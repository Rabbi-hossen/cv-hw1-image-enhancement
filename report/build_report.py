"""Build report/report.pdf from results/metrics.csv and results/figures/*.png.

Usage:  python report/build_report.py --name "Your Name" --repo "https://github.com/user/repo"
(requires `pip install reportlab`; only needed to rebuild the PDF, not the experiment)
"""
import argparse, csv, os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "results", "figures")
ap = argparse.ArgumentParser()
ap.add_argument("--name", default="[Your name]")
ap.add_argument("--repo", default="[repository URL]")
args = ap.parse_args()

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import glob
_d = [d for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu") if os.path.isdir(d)]
FN, FB, FI = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
if _d:
    for nm, fl in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf")):
        pdfmetrics.registerFont(TTFont(nm, os.path.join(_d[0], fl)))
    addMapping("DV", 0, 0, "DV"); addMapping("DV", 1, 0, "DV-B"); addMapping("DV", 0, 1, "DV-I"); addMapping("DV", 1, 1, "DV-BI")
    FN, FB, FI = "DV", "DV-B", "DV-I"

ss = getSampleStyleSheet()
B = ParagraphStyle("B", parent=ss["Normal"], fontName=FN, fontSize=8.2, leading=10.6, spaceAfter=3.5)
H = ParagraphStyle("H", parent=ss["Heading2"], fontName=FB, fontSize=10.5, keepWithNext=1, spaceBefore=6, spaceAfter=3)
T = ParagraphStyle("T", parent=ss["Title"], fontName=FB, fontSize=15, spaceAfter=2)
C = ParagraphStyle("C", parent=B, fontSize=7.8, leading=9.6, textColor=colors.HexColor("#333333"))
S = ParagraphStyle("S", parent=B, fontSize=7.4, leading=8.4)
W = 17.6 * cm

def fig(name, width, caption):
    from PIL import Image as PI
    w, h = PI.open(os.path.join(FIG, name)).size
    return KeepTogether([Image(os.path.join(FIG, name), width=width, height=width * h / w), Paragraph(caption, C), Spacer(1, 3)])

# ---------- metrics table ----------
rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "metrics.csv"))))
NAMES = {"degraded": "Degraded (baseline)", "stretch_lum": "Stretch, Lab-L", "stretch_rgb": "Stretch, per RGB ch.",
         "hist_eq": "Hist. eq., Lab-L", "stretch_nlm": "Stretch + NLM"}
data = [["Image", "Method", "PSNR (dB)", "SSIM", "MAE", "ΔE76"]]
best = {}
for r in rows:
    for k, hi in (("PSNR_dB", 1), ("SSIM", 1), ("MAE", 0), ("DeltaE76", 0)):
        v = float(r[k]); key = (r["image"], k)
        if key not in best or (v > best[key] if hi else v < best[key]):
            best[key] = v
style = [("FONT", (0, 0), (-1, -1), FN, 6.8), ("FONT", (0, 0), (-1, 0), FB, 6.8),
         ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDDDDD")), ("ALIGN", (2, 0), (-1, -1), "CENTER"),
         ("TOPPADDING", (0, 0), (-1, -1), 0.35), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.35),
         ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]
for i, r in enumerate(rows, start=1):
    cells = [r["image"] if r["method"] == "degraded" else "", NAMES[r["method"]]]
    for j, k in enumerate(("PSNR_dB", "SSIM", "MAE", "DeltaE76")):
        v = float(r[k]); s = f"{v:.4f}" if k == "SSIM" else f"{v:.2f}"
        if v == best[(r["image"], k)]:
            s = f"<b>{s}</b>"; 
        cells.append(Paragraph(s, ParagraphStyle("c", parent=S, alignment=1)))
    data.append(cells)
    if r["method"] == "degraded" and i > 1:
        style.append(("LINEABOVE", (0, i), (-1, i), 0.8, colors.black))
means = []
for m in NAMES:
    x = [r for r in rows if r["method"] == m]
    means.append([float(sum(float(q[k]) for q in x) / len(x)) for k in ("PSNR_dB", "SSIM", "MAE", "DeltaE76")])
style.append(("LINEABOVE", (0, len(rows) + 1), (-1, len(rows) + 1), 0.8, colors.black))
style.append(("FONT", (0, len(rows) + 1), (-1, -1), FI, 6.8))
for m, v in zip(NAMES, means):
    data.append(["mean (5 img.)" if m == "degraded" else "", NAMES[m], f"{v[0]:.2f}", f"{v[1]:.4f}", f"{v[2]:.2f}", f"{v[3]:.2f}"])
tbl = Table(data, colWidths=[2.3 * cm, 4.0 * cm, 2.2 * cm, 2.2 * cm, 2.0 * cm, 2.0 * cm], repeatRows=1)
tbl.setStyle(TableStyle(style))

src = [["File", "Source / author", "License", "Why chosen"],
       ["bottle.jpg", "Own photograph (the author)", "Own work; included for this assignment", "transparent bottle, specular highlights, fine label text; dark table vs. bright wall"],
       ["cap.jpg", "Own photograph (the author)", "Own work", "dark cap and shadow on a bright floor; fabric texture, small logo"],
       ["lamp.jpg", "Own photograph (the author)", "Own work", "black lamp against a bright curtain; strong brightness range, green frame (colour)"],
       ["mug.jpg", "Own photograph (the author)", "Own work", "white mug on a white wall with a soft shadow: intrinsically low contrast; hand/skin"],
       ["phone.jpg", "Own photograph (the author)", "Own work", "small keypad digits, uneven lighting with a bright specular blob on the desk"]]
src = [[Paragraph(str(c).replace("\n", "<br/>"), S) for c in r] for r in src]
st = Table(src, colWidths=[2.0 * cm, 3.6 * cm, 4.0 * cm, 8.0 * cm])
st.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDDDDD")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))

P = lambda t, s=B: Paragraph(t, s)
story = [
    P("Homework 1 – Image Enhancement with Classical Methods", T),
    P(f"Computer Vision, Fall 2026 &nbsp;|&nbsp; {args.name} &nbsp;|&nbsp; Code, data and results: {args.repo}", ParagraphStyle("a", parent=C, alignment=1)),
    P("1. Objective", H),
    P("We build and compare a small classical pipeline (OpenCV + NumPy, no learning-based methods) that enhances images with low contrast "
      "and noise. The aim is not a perfect reconstruction but to justify choices and observe the trade-offs between detail visibility, "
      "noise and natural appearance. Because the degradations are <b>synthetic</b>, the original photographs serve as <b>references</b> for the metrics; "
      "in real-world cases a clean reference is generally <b>not available</b>, so the numbers are only a proxy of perceived quality."),
    P("2. Data, sources and degradation", H),
    st, Spacer(1, 3),
    P("All five images are the author’s own real photographs (indoor scenes, smartphone camera, not synthetic), included in the repository. The raw "
      "1659×2212 photos are in <font face='Courier'>data/raw</font>; they were downscaled once to 600×800 (INTER_AREA, "
      "<font face='Courier'>src/prepare_images.py</font>) and these are the “originals”. They are reasonably exposed, so poor visibility is "
      "produced by a fixed, reproducible degradation (<font face='Courier'>src/degradation.py</font>): (i) contrast reduction "
      "<i>I′ = μ + 0.4 (I − μ)</i>, with μ the global mean of the image; (ii) additive zero-mean Gaussian noise with σ = 4 gray levels "
      "(0–255 scale), generated with <font face='Courier'>np.random.default_rng(42)</font>; (iii) clipping and rounding to 8 bit. Original and degraded "
      "versions are both kept. Scaling RGB also scales chroma by 0.4, so colours become washed out too."),
    P("3. Methods and parameters (identical for every image)", H),
    P("<b>M1 Baseline:</b> the degraded image. "
      "<b>M2 Linear contrast stretching:</b> the 1st–99th percentile of the Lab <i>L</i> channel is mapped to [0,255] and clipped; "
      "<i>a, b</i> are unchanged (luminance-only, so hue is preserved by construction). As a variant (M2b) each B, G, R channel is stretched independently, to "
      "study colour shifts. "
      "<b>M3 Histogram equalization:</b> <font face='Courier'>cv2.equalizeHist</font> on the Lab <i>L</i> channel (global; a, b unchanged). "
      "<b>M4 Motivated combination, stretch + denoising:</b> M2 followed by non-local means "
      "(<font face='Courier'>fastNlMeansDenoisingColored</font>, h = hColor = 8, template 7, search 21). Motivation: stretching multiplies the noise by the "
      "same gain as the signal (about 1/0.4 = 2.5), so noise is removed afterwards; this inevitably also smooths fine detail. "
      "<b>Metrics</b> (vs. the original, 8-bit): PSNR (mandatory), SSIM (scikit-image, multichannel), mean absolute error (MAE) and mean CIE76 colour difference ΔE."),
    P("4. Results", H),
    P("<b>Overview (Table 1, Fig. 1).</b> Averaged over the five images, stretch + NLM obtains the best SSIM (0.895 vs. 0.736 for the baseline) and the best mean PSNR among the "
      "luminance-based methods (20.77 vs. 18.97 dB, +1.8 dB) and the lowest ΔE (12.19). The plain Lab-L stretch gains 1.1 dB but <i>loses</i> a lot of SSIM (0.488) because it amplifies noise "
      "by about 2.5×. Histogram equalization is on average worse than doing nothing (15.07 dB, SSIM 0.283, ΔE 19.8). The per-channel stretch has the highest mean PSNR (21.16 dB) but "
      "a larger colour error than the baseline (ΔE 14.88 vs. 13.59). So no method is chosen from a single metric."),
    KeepTogether([P("<b>Table 1.</b> Metrics against the original (bold = best per image and metric; higher is better for PSNR/SSIM, lower for MAE/ΔE). "
      "Full CSV: <font face='Courier'>results/metrics.csv</font>.", C), tbl]), Spacer(1, 6),
    fig("comparison_all.png", 10.6 * cm, "<b>Figure 1.</b> Side-by-side comparison: original, degraded, and three enhancement results (same display scale for all panels). "
        "Per-image figures and the per-RGB-channel variant are in <font face='Courier'>results/</font>."),
    fig("crops_all.png", 14.2 * cm, "<b>Figure 2.</b> Zoomed crops (nearest-neighbour upsampling) showing noise amplification (stretch, hist. eq.) and detail loss after NLM."),
    fig("color_shift.png", 7.6 * cm, "<b>Figure 3.</b> Colour behaviour of the two stretching variants: luminance-only stretch (centre) leaves colours washed out; "
        "per-channel stretch (right) restores saturation but shifts colour balance (pinkish curtain in the lamp image)."),
    P("5. Discussion", H),
    P("<b>Case 1: numerical improvement ≠ visual improvement (mug).</b> The <i>mug</i> is a white object on a white wall; the original has very little contrast (std of L = 12.0). The unprocessed degraded image "
      "has the highest PSNR (22.12 dB) and every enhancement is <i>worse</i>: stretch 18.46 dB, NLM 19.29 dB, hist. eq. only 11.25 dB, although visually the enhanced images show the mug edge, the "
      "shadow and the skin texture of the hand more clearly (Figs. 1–2). The stretch expands the image to std 20.2 (hist. eq.: 29.4), i.e. far beyond the reference, so the pixel-wise error to "
      "the reference grows: PSNR measures fidelity to the reference, not visibility. The reverse also happens: NLM reaches SSIM 0.930 on the mug (baseline 0.768), but this is "
      "dominated by the huge flat wall, while the crop shows the fingertip texture smeared and darkened. Likewise on the <i>bottle</i> the stretch gains +0.5 dB PSNR while SSIM falls from "
      "0.745 to 0.439 because of noise in the flat wall. With no clean reference (the real-world case) none of these numbers could be computed."),
    P("<b>Case 2: lamp and phone.</b> <i>Lamp</i>: preferred method is <b>stretch + NLM</b> (best PSNR 23.56 dB, SSIM 0.893, ΔE 8.93). The curtain pleats, the window frame and the lamp arms "
      "are much easier to see, the noise on the bright curtain is removed and the shade edge and highlight remain sharp; the price is a slight loss of the fabric weave. Hist. eq. "
      "brightens the curtain and amplifies its noise (Fig. 2). <i>Phone</i>: the keypad digits 1–9 are barely legible in the degraded image; the stretch makes them clear, hist. eq. also does "
      "but turns the desk dark brown and fills the keypad with speckle noise, while stretch + NLM keeps the digits readable and suppresses the speckle (the real paint specks of the phone body are "
      "partly smoothed away too). The per-channel stretch gives the best numbers on the phone (26.6 dB, ΔE 9.8) because it restores the warm saturated wood lost in the degradation, but this is partly "
      "because the degradation scaled all channels uniformly."),
    P("<b>Colour and other artifacts.</b> The luminance-only stretch preserves hue (a, b untouched) but not saturation, so colours stay washed out (Fig. 3: the green frame of the lamp is dull, the desk "
      "of the phone is grayish-brown). The per-channel stretch restores saturation but changes the colour balance of neutral areas: on <i>cap</i>, <i>mug</i> and <i>lamp</i> its ΔE is higher than "
      "that of the Lab-L stretch (17.8, 17.1, 13.9 vs. 13.0, 11.6, 10.2), and the white curtain of the lamp gets a pinkish tint. Hist. eq. changes the look of whole regions: large uniform areas "
      "(floor of the <i>cap</i>, wall of the <i>mug</i>, table of the <i>bottle</i>) receive a wide range of output levels, which turns their noise into visible grain. No halos appear, since all "
      "methods are global; the visible artifacts are noise amplification, clipping of bright areas (the bright walls become nearly white after the stretch) and, with NLM, loss of fine texture."),
    P("<b>Limitations.</b> Only five images and one degradation setting; parameters were fixed a priori rather than tuned; global methods cannot treat strongly non-uniform illumination "
      "locally (CLAHE or a homomorphic filter would be natural next steps, with the risk of halos); PSNR/SSIM/MAE/ΔE are only proxies of perceived quality. <b>Conclusion:</b> a luminance-only "
      "stretch followed by mild denoising gave the best compromise here; histogram equalization should be avoided on noisy images dominated by large uniform areas."),
    P("References", H),
    P("Bradski, G. (2000), The OpenCV Library. · van der Walt et al. (2014), scikit-image: image processing in Python, PeerJ 2:e453 (SSIM implementation). · "
      "Buades, Coll, Morel (2005), A non-local algorithm for image denoising, CVPR. · Wang et al. (2004), Image quality assessment: from error visibility to structural similarity, IEEE TIP. · "
      "Gonzalez, Woods, Digital Image Processing (histogram processing, contrast stretching).", S),
]
out = os.path.join(ROOT, "report", "report.pdf")
doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm, topMargin=1.4 * cm, bottomMargin=1.4 * cm,
                        title="Homework 1 - Image Enhancement", author=args.name)
doc.build(story)
print("wrote", out)
