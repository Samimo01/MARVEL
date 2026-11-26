"""Logique métier du module financial_donations."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.modules.auth import repository as auth_repo
from app.modules.auth.models import User
from app.modules.campaigns import repository as campaign_repo
from app.modules.financial_donations import repository as don_repo
from app.modules.financial_donations.models import FinancialDon
from app.modules.financial_donations.schemas import (
    FinancialDonCreate,
    FinancialDonOut,
    PaymentInitOut,
    PaymentStatusOut,
)


class DonationNotFoundError(Exception):
    pass


class CampaignNotFoundError(Exception):
    pass


class DonationAlreadyPaidError(Exception):
    pass


class DonationNotSuccessfulError(Exception):
    pass


def _get_or_raise(session: Session, id_don_f: UUID) -> FinancialDon:
    don = don_repo.get_donation_by_id(session, id_don_f)
    if don is None:
        raise DonationNotFoundError(f"Don {id_don_f} introuvable")
    return don


def create_financial_donation(
    session: Session, *, user: User, payload: FinancialDonCreate
) -> FinancialDonOut:
    campaign = campaign_repo.get_campaign_by_id(session, payload.id_campaign)
    if not campaign:
        raise CampaignNotFoundError("Campagne introuvable")

    donation = FinancialDon(
        id_user=user.id_user if not payload.is_anonymous else None,
        id_campaign=payload.id_campaign,
        amount=payload.amount,
        is_anonymous=payload.is_anonymous,
        status="Pending",
    )
    don_repo.add_donation(session, donation)
    session.commit()
    session.refresh(donation)
    return FinancialDonOut.model_validate(donation)


def pay_donation(session: Session, *, user: User, id_don_f: UUID) -> PaymentInitOut:
    donation = _get_or_raise(session, id_don_f)

    if donation.status == "Success":
        raise DonationAlreadyPaidError("Ce don a déjà été payé.")

    mock_payment_url = f"https://mock-payment-gateway.com/pay/{id_don_f}"
    reference = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    donation.reference_payment = reference

    don_repo.update_donation(session, donation, {"reference_payment": reference})
    session.commit()

    return PaymentInitOut(
        id_don_f=donation.id_don_f,
        payment_url=mock_payment_url,
        message="Session de paiement ouverte. Utilisez l'URL pour finaliser.",
    )


def get_payment_status(session: Session, id_don_f: UUID) -> PaymentStatusOut:
    donation = _get_or_raise(session, id_don_f)

    if donation.reference_payment and donation.status != "Success":
        donation.status = "Success"
        donation.paid_at = datetime.now(UTC)
        don_repo.update_donation(
            session,
            donation,
            {
                "status": "Success",
                "paid_at": donation.paid_at,
            },
        )
        session.commit()
        session.refresh(donation)

    return PaymentStatusOut(
        id_don_f=donation.id_don_f,
        status=donation.status,
        reference_payment=donation.reference_payment,
        paid_at=donation.paid_at,
    )


def list_my_donations(session: Session, *, user: User) -> list[FinancialDonOut]:
    dons = don_repo.list_user_donations(session, user.id_user)
    return [FinancialDonOut.model_validate(d) for d in dons]


def get_donation_detail(session: Session, id_don_f: UUID) -> FinancialDonOut:
    donation = _get_or_raise(session, id_don_f)
    return FinancialDonOut.model_validate(donation)



def list_donations(
    session: Session,
    *,
    status: str | None = None,
    id_campaign: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FinancialDonOut]:
    dons = don_repo.list_all_donations(
        session,
        status=status,
        id_campaign=id_campaign,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return [FinancialDonOut.model_validate(d) for d in dons]


def list_successful_donations(
    session: Session,
) -> list[FinancialDonOut]:
    dons = don_repo.list_successful_donations(session)
    return [FinancialDonOut.model_validate(d) for d in dons]


def list_successful_donations_by_campaign(
    session: Session, id_campaign: UUID
) -> list[FinancialDonOut]:
    dons = don_repo.list_successful_donations_by_campaign(session, id_campaign)
    return [FinancialDonOut.model_validate(d) for d in dons]


def get_campaign_amount_collected(session: Session, id_campaign: UUID) -> Decimal:
    """Expose le calcul du montant collecté pour une campagne."""
    return don_repo.get_campaign_amount_collected(session, id_campaign)


def get_campaigns_amounts_collected(session: Session, ids: list[UUID]) -> dict[UUID, Decimal]:
    """Expose le calcul batch des montants collectés."""
    return don_repo.get_campaigns_amounts_collected(session, ids)


def list_campaign_donations(session: Session, id_campaign: UUID) -> list[FinancialDonOut]:
    """Expose la liste des dons d'une campagne."""
    dons = don_repo.list_donations_by_campaign(session, id_campaign)
    return [FinancialDonOut.model_validate(d) for d in dons]

"""Génération de reçus PDF (retourne bytes, pas de fichier)."""


def generate_receipt_pdf(data: dict) -> bytes:
    """
    Génère un reçu PDF et retourne les bytes.

    Args:
        data: dict avec les clés :
            - id_don_f (str)
            - reference (str)
            - donor_name (str)
            - campaign_title (str)
            - amount (Decimal | float)
            - paid_at (str)
            - status (str)
            - generated_at (str)

    Returns:
        bytes: contenu du PDF.
    """
    output = BytesIO()

    # Couleurs MARVEL
    NAVY = colors.HexColor("#17335A")
    ORANGE = colors.HexColor("#EA580C")
    GREEN = colors.HexColor("#15803D")
    LIGHT_BLUE = colors.HexColor("#EAF0F7")
    DARK_GREY = colors.HexColor("#475569")

    # Document (portrait pour un reçu)
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Reçu de don {data['reference']}",
        author="MARVEL",
        subject="Reçu de don financier",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=NAVY,
    )
    ref_style = ParagraphStyle(
        "ReceiptRef",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=DARK_GREY,
        alignment=2,  # right
    )
    label_style = ParagraphStyle(
        "ReceiptLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_GREY,
    )
    value_style = ParagraphStyle(
        "ReceiptValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=NAVY,
    )
    amount_style = ParagraphStyle(
        "ReceiptAmount",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=GREEN,
        alignment=1,  # center
    )
    footer_style = ParagraphStyle(
        "ReceiptFooter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=DARK_GREY,
        alignment=1,
    )

    elements = []

    # ── HEADER ──
    header = Table(
        [[
            Paragraph("REÇU DE DON", title_style),
            Paragraph(
                f"Réf : <b>{data['reference'] or 'N/A'}</b><br/>"
                f"Généré le {data['generated_at']}",
                ref_style,
            ),
        ]],
        colWidths=[10*cm, 7*cm],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 2, ORANGE),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 30))

    # ── BODY ──
    body_rows = [
        [Paragraph("Donateur :", label_style),
         Paragraph(data["donor_name"] or "Anonyme", value_style)],
        [Paragraph("Campagne :", label_style),
         Paragraph(data["campaign_title"] or "N/A", value_style)],
        [Paragraph("Date du paiement :", label_style),
         Paragraph(data["paid_at"], value_style)],
        [Paragraph("Statut :", label_style),
         Paragraph(f'<font color="#15803D"><b>{data["status"]}</b></font>', value_style)],
    ]
    body = Table(body_rows, colWidths=[5*cm, 12*cm])
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(body)
    elements.append(Spacer(1, 30))

    # ── MONTANT ──
    amount = Decimal(str(data["amount"]))
    amount_paragraph = Paragraph(f"{amount:,.2f} DZD".replace(",", " "), amount_style)
    amount_box = Table([[amount_paragraph]], colWidths=[16*cm])
    amount_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 1.5, NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 25),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 25),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(amount_box)
    elements.append(Spacer(1, 60))

    # ── FOOTER ──
    elements.append(Paragraph(
        "Ce reçu atteste de la réception du don mentionné ci-dessus.<br/>"
        "Document généré automatiquement — Ne nécessite pas de signature.",
        footer_style,
    ))

    # Build
    doc.build(elements)
    return output.getvalue()


def build_receipt(session: Session, id_don_f: UUID) -> tuple[bytes, str]:
    """
    DON-06 : Génère le reçu PDF EN MÉMOIRE.

    Aucun fichier n'est écrit sur le disque.

    Returns:
        (pdf_bytes, filename)
    """
    donation = _get_or_raise(session, id_don_f)

    if donation.status != "Success":
        raise DonationNotSuccessfulError(
            f"Impossible de générer un reçu pour un don au statut '{donation.status}'."
        )

    campaign = campaign_repo.get_campaign_by_id(session, donation.id_campaign)
    donor = (
        auth_repo.get_user_by_id(session, donation.id_user)
        if donation.id_user else None
    )

    pdf_bytes = generate_receipt_pdf({
        "id_don_f": str(donation.id_don_f),
        "reference": donation.reference_payment or "",
        "donor_name": f"{donor.firstname} {donor.lastname}" if donor else "Anonyme",
        "campaign_title": campaign.title if campaign else "N/A",
        "amount": donation.amount,
        "paid_at": (
            donation.paid_at.strftime("%d/%m/%Y à %H:%M")
            if donation.paid_at else "N/A"
        ),
        "status": donation.status,
        "generated_at": datetime.now(UTC).strftime("%d/%m/%Y à %H:%M"),
    })

    filename = f"recu-{donation.id_don_f}.pdf"
    return pdf_bytes, filename