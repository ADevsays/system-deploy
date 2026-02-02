import os
import logging

logger = logging.getLogger(__name__)

from app.core.video_styles import TextStyle

class AssService:
    @staticmethod
    def format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:01}:{minutes:02}:{secs:05.2f}"

    @staticmethod
    def generate_ass(
        output_path: str,
        text: str,
        duration: float,
        width: int,
        height: int,
        template: TextStyle
    ):
        """
        Generador de archivos .ass basado en un objeto de estilo abstracto.
        """
        end_time = AssService.format_time(duration)
        sanitized_text = text.replace("\n", "\\N").replace("\r", "")
        
        # Ajustar dinámicamente el tamaño de fuente si es necesario de forma proporcional
        # Pero respetamos el objeto de estilo recibido
        ass_style = template.to_ass_style_line()

        content = [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {width}",
            f"PlayResY: {height}",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Alignment, MarginL, MarginR, MarginV, Encoding",
            ass_style,
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
            # Nota: pos(x,y) sobrescribe el alineamiento del estilo para la posición exacta
            f"Dialogue: 0,0:00:00.00,{end_time},Custom,,0,0,0,,{{\\pos({template.pos_x},{template.pos_y})}}{sanitized_text}"
        ]

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            return output_path
        except Exception as e:
            logger.error(f"Error generando ASS con estilo {template}: {e}")
            raise e
