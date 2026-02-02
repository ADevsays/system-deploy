from dataclasses import dataclass, field
from enum import Enum

class VideoTemplate(str, Enum):
    MEME_CLASSIC = "meme_classic_bold"
    MEME_THIN = "meme_modern_thin"

@dataclass
class TextStyle:
    font_name: str = "Montserrat"
    primary_color: str = "&H00FFFFFF" 
    bold: bool = True
    outline: float = 0.6
    alignment: int = 5
    margin_h: int = 50
    margin_v: int = 0
    
    # Ratios relativos al tamaño del video
    font_size_ratio: float = 0.031
    pos_x_ratio: float = 0.5    # 540/1080
    pos_y_ratio: float = 0.234 # 570/1920
    
    # Campos que se calculan al vuelo
    font_size: int = field(init=False, default=60)
    pos_x: int = field(init=False, default=0)
    pos_y: int = field(init=False, default=0)

    def prepare_for_video(self, width: int, height: int):
        """
        Calcula los valores absolutos de fuente y posición basados en las dimensiones del video.
        """
        self.font_size = int(height * self.font_size_ratio)
        self.pos_x = int(width * self.pos_x_ratio)
        self.pos_y = int(height * self.pos_y_ratio)

    def to_ass_style_line(self, name: str = "Custom") -> str:
        bold_val = 1 if self.bold else 0
        return (
            f"Style: {name},{self.font_name},{self.font_size},{self.primary_color},&H000000FF,"
            f"{self.primary_color},&H00000000,{bold_val},0,0,0,100,100,0,0,1,{self.outline},"
            f"{self.alignment},{self.margin_h},{self.margin_h},{self.margin_v},1"
        )

# Diccionario de estilos para evitar magic strings y permitir escalabilidad
_STYLE_CATALOG = {
    VideoTemplate.MEME_CLASSIC: {
        "font_name": "Montserrat",
        "bold": True,
        "outline": 0.6,
        "alignment": 5,
        "margin_h": 50
    },
    VideoTemplate.MEME_THIN: {
        "font_name": "Arial",
        "bold": False,
        "outline": 0,
        "alignment": 5,
        "margin_h": 50
    }
}

class StyleRegistry:
    @staticmethod
    def resolve(template: VideoTemplate) -> TextStyle:
        """
        Handler que resuelve y devuelve un objeto TextStyle basado en el template.
        """
        config = _STYLE_CATALOG.get(template)
        if not config:
            # Fallback al estilo por defecto si no se encuentra
            config = _STYLE_CATALOG[VideoTemplate.MEME_CLASSIC]
            
        return TextStyle(**config)
