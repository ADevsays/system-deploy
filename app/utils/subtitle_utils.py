import os
import re

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"

def generate_youtube_clip_ass(
    output_path: str, 
    title: str, 
    yellow_word: str, 
    part: int, 
    width: int, 
    height: int,
    composition_mode: str = "normal",
    add_cta: bool = False,
    cta_start: float = 0.0,
    uploader: str = "",
    original_title: str = ""
):
    """
    Generates an .ass subtitle file with a top title and a bottom part indicator.
    """
    processed_title = title.upper().strip()
    
    if yellow_word:
        yw = yellow_word.upper().strip()
        escaped_yw = re.escape(yw)
        processed_title = re.sub(
            f"\\b{escaped_yw}\\b", 
            f"{{\\\\c&H0012C8F3&}}{yw}{{\\\\c&HFFFFFF&}}", 
            processed_title
        )

    title_size = int(height * 0.052)
    part_size = int(height * 0.038)
    
    top_margin = int(height * 0.11)
    bottom_margin = int(height * 0.04)

    if composition_mode == "fullscreen":
        outline = 3
        shadow = 12
    else:
        outline = 0
        shadow = 2

    if add_cta:
        main_end = format_timestamp(cta_start)
    else:
        main_end = "99:59:59.99"

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleStyle,Montserrat Bold,{title_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,-4,0,1,{outline},{shadow},8,0,0,{top_margin},1
Style: PartStyle,Montserrat Bold,{part_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,-4,0,1,{outline},{shadow},2,0,0,{bottom_margin},1
"""

    if add_cta:
        thumb_h = int((width * 0.8) * 9 / 16)
        thumb_top_y = (height - thumb_h) // 2
        thumb_bottom_y = (height + thumb_h) // 2
        font_size = int(width * 0.045)
        logo_w = int(font_size * 1.5)

        top_text_y = thumb_top_y - (font_size * 2) - 40
        inline_y = thumb_top_y - font_size - 20
        bottom_text_y = thumb_bottom_y + 40

        char_w = int(font_size * 0.55)
        clean_uploader = uploader.upper().strip().replace("{", "").replace("}", "")
        clean_title = original_title.upper().strip().replace("{", "").replace("}", "")
        text_w = len(clean_uploader) * char_w
        gap = int(font_size * 0.4)
        total_inline_w = logo_w + gap + text_w
        start_x = (width - total_inline_w) // 2
        text_x = start_x + logo_w + gap

        ass_content += f"""Style: CTATop,Montserrat Bold,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,-4,0,1,0,3,8,0,0,{top_text_y},1
Style: CTAUploader,Montserrat Bold,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,-4,0,1,0,3,7,{text_x},0,{inline_y},1
Style: CTATitle,Montserrat Bold,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,-4,0,1,0,3,8,0,0,{bottom_text_y},1
"""

    ass_content += f"""
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,{main_end},TitleStyle,,0,0,0,,{processed_title}
Dialogue: 0,0:00:00.00,{main_end},PartStyle,,0,0,0,,PARTE {part}
"""

    if add_cta:
        cta_s = format_timestamp(cta_start)
        ass_content += f"""Dialogue: 0,{cta_s},99:59:59.99,CTATop,,0,0,0,,MIRA EL VÍDEO {{\\c&H0012C8F3&}}COMPLETO{{\\c&HFFFFFF&}} EN
Dialogue: 0,{cta_s},99:59:59.99,CTAUploader,,0,0,0,,{clean_uploader}
Dialogue: 0,{cta_s},99:59:59.99,CTATitle,,0,0,0,,{clean_title}
"""

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(ass_content)

    return output_path
