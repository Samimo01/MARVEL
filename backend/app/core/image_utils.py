"""Utilitaires de traitement d'images."""

from io import BytesIO

from PIL import Image, UnidentifiedImageError


class InvalidImageError(ValueError):
    """Levée quand les bytes fournis ne sont pas une image décodable."""
    pass


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
    - Lève `InvalidImageError` si les bytes ne sont pas une image valide.
    """
    if not image_bytes:
        raise InvalidImageError("Fichier image vide.")

    # ── Décodage robuste ──
    try:
        img = Image.open(BytesIO(image_bytes))
        img.load()          # force le décodage complet (sinon erreur tardive au .save())
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError(
            "Image invalide ou corrompue : impossible de la décoder."
        ) from exc

    # Convertir en RGB si nécessaire
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # Redimensionner si trop large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # Sauvegarder en WebP
    output = BytesIO()
    try:
        img.save(output, format="WEBP", quality=quality, method=6)
    except OSError as exc:
        raise InvalidImageError(
            "Échec de la conversion en WebP."
        ) from exc

    return output.getvalue()