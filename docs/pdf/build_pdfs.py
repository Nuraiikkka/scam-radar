import re
from pathlib import Path

from fpdf import FPDF

PDF_DIR = Path(__file__).resolve().parent
GUIDES = ["guide_nuray", "guide_aisulu", "guide_moldir", "guide_adiya"]
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]


def find_font() -> str:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("No font with Cyrillic letters found. Install fonts-dejavu-core.")


def plain(text: str) -> str:
    text = text.replace("**", "")
    return re.sub(r"`([^`]*)`", r"\1", text)


def render(pdf: FPDF, markdown: str) -> None:
    in_code = False
    for line in markdown.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            pdf.ln(1)
            continue
        if in_code:
            pdf.set_font("Main", size=9)
            pdf.set_fill_color(240, 240, 240)
            pdf.multi_cell(0, 5, line, fill=True, new_x="LMARGIN", new_y="NEXT", align="L")
            continue
        if line.startswith("# "):
            pdf.set_font("Main", size=16)
            pdf.multi_cell(0, 9, plain(line[2:]), new_x="LMARGIN", new_y="NEXT", align="L")
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.ln(2)
            pdf.set_font("Main", size=13)
            pdf.multi_cell(0, 7, plain(line[3:]), new_x="LMARGIN", new_y="NEXT", align="L")
        elif line.startswith("- "):
            pdf.set_font("Main", size=10.5)
            pdf.multi_cell(0, 5.5, "•  " + plain(line[2:]), new_x="LMARGIN", new_y="NEXT", align="L")
        elif line.strip() == "":
            pdf.ln(2)
        else:
            pdf.set_font("Main", size=10.5)
            pdf.multi_cell(0, 5.5, plain(line), new_x="LMARGIN", new_y="NEXT", align="L")


def build(name: str, font: str) -> Path:
    pdf = FPDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(True, margin=16)
    pdf.add_font("Main", "", font)
    pdf.add_page()
    render(pdf, (PDF_DIR / (name + ".md")).read_text(encoding="utf-8"))
    target = PDF_DIR / (name + ".pdf")
    pdf.output(str(target))
    return target


def main() -> None:
    font = find_font()
    for name in GUIDES:
        print("wrote " + str(build(name, font)))


if __name__ == "__main__":
    main()
