"""Huella perceptual de imágenes (dHash) para detectar fotos repetidas o muy parecidas."""
import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Protege contra "bombas de descompresión" (imágenes diminutas en disco que ocupan gigas en memoria).
Image.MAX_IMAGE_PIXELS = 40_000_000

MAX_LADO = 1600  # px del lado mayor al guardar las fotos

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


def a_entero(h):
    """Huella hexadecimal -> entero (None si falta). Se convierte una sola vez por huella."""
    return int(h, 16) if h else None


def distancia_enteros(a, b):
    """Distancia de Hamming entre dos huellas ya convertidas a entero (64 si falta alguna)."""
    if a is None or b is None:
        return 64
    return (a ^ b).bit_count()


def optimizar_imagen(archivo, max_lado=MAX_LADO, calidad=85):
    """Reduce el peso de una foto: corrige la orientación, limita el lado mayor y guarda como JPEG.

    Devuelve un ContentFile .jpg; si algo falla devuelve el archivo original sin tocar.
    """
    try:
        archivo.seek(0)
        img = ImageOps.exif_transpose(Image.open(archivo))
        if img.mode in ("RGBA", "LA", "P"):  # sin transparencia en JPEG: fondo blanco
            img = img.convert("RGBA")
            fondo = Image.new("RGB", img.size, "white")
            fondo.paste(img, mask=img.getchannel("A"))
            img = fondo
        else:
            img = img.convert("RGB")
        img.thumbnail((max_lado, max_lado), Image.LANCZOS)
        salida = BytesIO()
        img.save(salida, "JPEG", quality=calidad, optimize=True)
        base = os.path.splitext(os.path.basename(getattr(archivo, "name", "") or "foto"))[0] or "foto"
        return ContentFile(salida.getvalue(), name=f"{base}.jpg")
    except Exception:
        try:
            archivo.seek(0)
        except Exception:
            pass
        return archivo
