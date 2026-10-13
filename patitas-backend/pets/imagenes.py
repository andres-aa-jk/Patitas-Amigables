"""Huella perceptual de imágenes (dHash) para detectar fotos repetidas o muy parecidas."""
from PIL import Image

UMBRAL_DUPLICADO = 10  # distancia de Hamming máxima (de 64 bits) para sugerir duplicado


def calcular_hash(archivo):
    """Devuelve una huella de 64 bits en hexadecimal, o '' si no es una imagen válida."""
    try:
        archivo.seek(0)
        img = Image.open(archivo).convert("L").resize((9, 8), Image.LANCZOS)
        px = list(img.getdata())
        bits = 0
        for fila in range(8):
            for col in range(8):
                bits = (bits << 1) | (px[fila * 9 + col] > px[fila * 9 + col + 1])
        archivo.seek(0)
        return f"{bits:016x}"
    except Exception:
        try:
            archivo.seek(0)
        except Exception:
            pass
        return ""


def distancia(h1, h2):
    """Distancia de Hamming entre dos huellas (64 si alguna falta)."""
    if not h1 or not h2:
        return 64
    return bin(int(h1, 16) ^ int(h2, 16)).count("1")
