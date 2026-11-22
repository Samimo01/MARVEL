"""Utilitaires de traitement d'images."""

from io import BytesIO

from PIL import Image


def convert_image_to_webp(
    image_bytes: bytes,
    *,
    quality: int = 80,
    max_width: int = 1600,
) -> bytes:
    """
    Convertit une image (JPEG, PNG, etc.) en WebP.

    - Redimensionne si la largeur dépasse `max_width` (préserve le ratio).
    - Retourne les bytes de l'image WebP.
    """
    img = Image.open(BytesIO(image_bytes))

    # Convertir en RGB si nécessaire (ex: PNG avec transparence -> RGB pour WebP)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # Redimensionner si trop large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # Sauvegarder en WebP dans un buffer
    output = BytesIO()
    img.save(output, format="WEBP", quality=quality, method=6)
    return output.getvalue()
