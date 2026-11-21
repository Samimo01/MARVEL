"""Endpoints HTTP du module treasury."""

import csv
from io import BytesIO, StringIO

from fastapi.responses import Response

from openpyxl import Workbook

from reportlab.lib import colors
from openpyxl.styles import PatternFill, Font
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.dependencies import require_treasury_staff
from app.database import get_db
from app.modules.auth.models import User
from app.modules.treasury import service as treasury_service
from app.modules.treasury.schemas import (
    BudgetSummaryOut,
    CampaignDonationsTotalOut,
    CampaignEventsGainsOut,
    CampaignGainsOut,
    EventGainsOut,
    ExpenseOut,
    ExpenseUpdate,
    FundOut,
    SystemCampaignGainsOut,
)
from app.modules.treasury.service import (
    CampaignNotFoundError,
    EventNotFoundError,
    FundNotFoundError,
    InvalidExpenseError,
    get_campaign_event_gains,
)



router = APIRouter(tags=["Treasury"])



def generate_csv(data: dict) -> bytes:
    """Génère un export CSV du bilan budgétaire et des opérations."""

    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    if "budget" in data:
        writer.writerow(["BILAN BUDGETAIRE"])
        writer.writerow(["Indicateur", "Montant"])

        for key, value in data["budget"].items():
            writer.writerow([key, value])

        writer.writerow([])

    if "operations" in data:
        writer.writerow(["OPERATIONS FINANCIERES"])
        writer.writerow([
            "ID",
            "Montant",
            "Catégorie",
            "Date",
            "Justificatif",
            "ID événement",
        ])

        for item in data["operations"]:
            writer.writerow([
                item["id_fund"],
                item["amount"],
                item["category"],
                item["transaction_at"],
                item["justificative"],
                item["id_event"],
            ])

    return output.getvalue().encode("utf-8-sig")


def generate_xlsx(data: dict) -> bytes:
    """Génère un fichier Excel avec le bilan budgétaire et les opérations."""

    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    header_fill = PatternFill(
        start_color="17335A",
        end_color="17335A",
        fill_type="solid",
    )
    header_font = Font(color="FFFFFF", bold=True)

    def create_sheet(title: str, headers: list, rows: list):
        sheet = workbook.create_sheet(title=title)
        sheet.append(headers)

        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font

        for row in rows:
            sheet.append(row)

        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

        for column in sheet.columns:
            max_length = max(
                len(str(cell.value or "")) for cell in column
            )
            sheet.column_dimensions[column[0].column_letter].width = min(
                max_length + 3, 45
            )

    if "budget" in data:
        create_sheet(
            "Bilan budgétaire",
            ["Indicateur", "Montant"],
            [[key, float(value)] for key, value in data["budget"].items()],
        )

    if "operations" in data:
        create_sheet(
            "Opérations",
            [
                "ID",
                "Montant",
                "Catégorie",
                "Date",
                "Justificatif",
                "ID événement",
            ],
            [
                [
                    item["id_fund"],
                    float(item["amount"]),
                    item["category"],
                    item["transaction_at"].isoformat(),
                    item["justificative"],
                    item["id_event"],
                ]
                for item in data["operations"]
            ],
        )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return output.getvalue()


def generate_pdf(data: dict) -> bytes:
    """Génère un rapport PDF du bilan budgétaire et des opérations."""

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Rapport de trésorerie", styles["Title"]))
    elements.append(Spacer(1, 20))

    def add_table(title: str, headers: list, rows: list):
        elements.append(Paragraph(title, styles["Heading2"]))

        table_data = [headers] + [
            [str(value) if value is not None else "" for value in row]
            for row in rows
        ]

        table = Table(table_data, repeatRows=1)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17335A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#F0F4F8"),
            ]),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 18))

    if "budget" in data:
        add_table(
            "Bilan budgétaire",
            ["Indicateur", "Montant"],
            [[key, value] for key, value in data["budget"].items()],
        )

    if "operations" in data:
        add_table(
            "Opérations financières",
            [
                "ID",
                "Montant",
                "Catégorie",
                "Date",
                "Justificatif",
                "ID événement",
            ],
            [
                [
                    item["id_fund"],
                    item["amount"],
                    item["category"],
                    item["transaction_at"].strftime("%d/%m/%Y %H:%M"),
                    item["justificative"],
                    item["id_event"],
                ]
                for item in data["operations"]
            ],
        )

    document.build(elements)
    output.seek(0)

    return output.getvalue()


# ============================================================
# TRE-01 : GET /funds
# ============================================================

@router.get("/funds", response_model=list[FundOut])
def tre01_list_funds(
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    return treasury_service.list_funds(session)


# ============================================================
# TRE-02 : GET /funds/{id_fund}
# ============================================================

@router.get("/funds/{id_fund}", response_model=FundOut)
def tre02_get_fund_detail(
    id_fund: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    try:
        return treasury_service.get_fund_detail(session, id_fund)
    except FundNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# TRE-03 : POST /funds/{id_event}/expenses
# ============================================================

@router.post(
    "/funds/{id_event}/expenses",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
async def tre03_create_expense(
    id_event: UUID,
    amount: Decimal = Form(..., gt=0),
    category: str = Form(..., min_length=1),
    transaction_at: datetime = Form(...),
    justificative: str | None = Form(None),
    image: UploadFile | None = File(None),
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    if image and not image.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    image_bytes = await image.read() if image else None

    from app.modules.treasury.schemas import ExpenseCreate

    payload = ExpenseCreate(
        amount=amount,
        category=category,
        transaction_at=transaction_at,
        justificative=justificative,
    )

    try:
        return treasury_service.create_expense(
            session,
            user=user,
            id_event=id_event,
            payload=payload,
            image_bytes=image_bytes,
        )
    except EventNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidExpenseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


# ============================================================
# TRE-04 : GET /funds/{id_event}/expenses
# ============================================================

@router.get(
    "/funds/{id_event}/expenses",
    response_model=list[ExpenseOut],
)
def tre04_list_expenses(
    id_event: UUID,
    category: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    try:
        return treasury_service.list_expenses(
            session,
            id_event,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
    except EventNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidExpenseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


# ============================================================
# TRE-05 : PUT /funds/{id_event}/expenses/{id_fund}
# ============================================================

@router.put(
    "/funds/{id_event}/expenses/{id_fund}",
    response_model=ExpenseOut,
)
async def tre05_update_expense(
    id_event: UUID,
    id_fund: UUID,
    amount: Decimal | None = Form(None, gt=0),
    category: str | None = Form(None, min_length=1),
    transaction_at: datetime | None = Form(None),
    justificative: str | None = Form(None),
    image: UploadFile | None = File(None),
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    if image and not image.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    data = {
        key: value
        for key, value in {
            "amount": amount,
            "category": category,
            "transaction_at": transaction_at,
            "justificative": justificative,
        }.items()
        if value is not None
    }

    image_bytes = await image.read() if image else None

    if not data and image_bytes is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Au moins un champ ou une nouvelle photo doit être fourni.",
        )

    # Une justification textuelle vide permet aussi de supprimer
    # l'ancienne justification.
    if image_bytes is not None and not data:
        data["justificative"] = None

    payload = ExpenseUpdate(**data)

    try:
        return treasury_service.update_expense(
            session,
            id_event=id_event,
            id_fund=id_fund,
            payload=payload,
            image_bytes=image_bytes,
        )
    except FundNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidExpenseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


# ============================================================
# TRE-06 : GET /treasury/budget
# ============================================================

@router.get("/treasury/budget", response_model=BudgetSummaryOut)
def tre06_get_budget_summary(
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    return treasury_service.get_budget_summary(session)


# ============================================================
# TRE-07 : GET /treasury/export
# ============================================================

@router.get("/treasury/export")
def tre07_export_treasury(
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    type: str = Query("all", pattern="^(all|budget|operations)$"),
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    data = treasury_service.get_export_data(session, type)

    if format == "csv":
        content = generate_csv(data)
        media_type = "text/csv"
        filename = "rapport_tresorerie.csv"

    elif format == "xlsx":
        content = generate_xlsx(data)
        media_type = (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
        filename = "rapport_tresorerie.xlsx"

    else:
        content = generate_pdf(data)
        media_type = "application/pdf"
        filename = "rapport_tresorerie.pdf"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
    

# ============================================================
# TRE-08 : GET /treasury/budget_compaigns/{id_campaign}
# ============================================================

@router.get(
    "/treasury/budget_compaigns/{id_campaign}",
    response_model=CampaignGainsOut,
)
def tre08_get_campaign_gains(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    try:
        return treasury_service.get_campaign_gains(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    

# ============================================================
# TRE-09 : GET /treasury/budget_compaigns/
# ============================================================

@router.get(
    "/treasury/budget_compaigns/",
    response_model=list[SystemCampaignGainsOut],
)
def tre09_get_system_campaigns_gains(
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    return treasury_service.get_system_campaigns_gains(session)


# ============================================================
# TRE-10 : GET /treasury/budget_compaigns/{id_campaign}/event/{id_event}
# ============================================================

@router.get(
    "/treasury/budget_compaigns/{id_campaign}/event/{id_event}",
    response_model=EventGainsOut,
)
def tre10_get_campaign_event_gains(
    id_campaign: UUID,
    id_event: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    try:
        return treasury_service.get_campaign_event_gains(
            session,
            id_campaign,
            id_event,
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    

# ============================================================
# TRE-11 : GET /treasury/budget_compaigns/{id_campaign}/dons
# ============================================================

@router.get(
    "/treasury/budget_compaigns/{id_campaign}/dons",
    response_model=CampaignDonationsTotalOut,
)
def tre11_get_campaign_donations_total(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    try:
        return treasury_service.get_campaign_donations_total(
            session, id_campaign
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# TRE-12 : GET /treasury/budget_compaigns/{id_campaign}/event
# ============================================================

@router.get(
    "/treasury/budget_compaigns/{id_campaign}/event",
    response_model=CampaignEventsGainsOut,
)
def tre12_get_campaign_events_gains(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_treasury_staff),
):
    try:
        return treasury_service.get_campaign_events_gains(
            session, id_campaign
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc