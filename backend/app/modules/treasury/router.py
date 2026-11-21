"""Endpoints HTTP du module treasury."""
# ============================================================
# Bibliothèques standard Python
# ============================================================
import csv

from datetime import datetime
from decimal import Decimal
from io import BytesIO, StringIO
from uuid import UUID


# ============================================================
# FastAPI
# ============================================================
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
from fastapi.responses import Response


# ============================================================
# SQLAlchemy
# ============================================================
from sqlalchemy.orm import Session


# ============================================================
# OpenPyXL - Génération des fichiers Excel
# ============================================================
from openpyxl import Workbook
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import CellIsRule


# ============================================================
# ReportLab - Génération des fichiers PDF
# ============================================================
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    LongTable,
    PageBreak,
    Table as PDFTable,
    TableStyle,
)


# ============================================================
# Modules internes du projet
# ============================================================
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
    """Génère un classeur Excel professionnel pour le rapport de trésorerie."""

    workbook = Workbook()
    workbook.remove(workbook.active)

    # Identité visuelle MARVEL
    NAVY = "17335A"
    ORANGE = "EA580C"
    WHITE = "FFFFFF"
    LIGHT_BLUE = "EAF0F7"
    LIGHT_GREY = "F4F6F9"
    DARK_GREY = "475569"
    GREEN = "15803D"
    RED = "DC2626"

    currency_format = '#,##0.00 "DZD"'
    date_format = "DD/MM/YYYY HH:MM"

    thin_grey = Side(style="thin", color="DCE3EC")

    generated_at = datetime.now()

    def configure_sheet(sheet):
        sheet.sheet_view.showGridLines = False
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
        sheet.sheet_properties.outlinePr.summaryBelow = True

    def style_title(sheet, cell_range, title):
        sheet.merge_cells(cell_range)
        cell = sheet[cell_range.split(":")[0]]
        cell.value = title
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(name="Aptos Display", size=20, bold=True, color=WHITE)
        cell.alignment = Alignment(vertical="center")
        sheet.row_dimensions[cell.row].height = 42

    def style_subtitle(sheet, cell_range, subtitle):
        sheet.merge_cells(cell_range)
        cell = sheet[cell_range.split(":")[0]]
        cell.value = subtitle
        cell.font = Font(name="Aptos", size=10, color=DARK_GREY, italic=True)
        cell.alignment = Alignment(vertical="center")
        sheet.row_dimensions[cell.row].height = 25

    def add_kpi(sheet, label_range, value_range, label, value, color=NAVY):
        sheet.merge_cells(label_range)
        sheet.merge_cells(value_range)

        label_cell = sheet[label_range.split(":")[0]]
        value_cell = sheet[value_range.split(":")[0]]

        label_cell.value = label.upper()
        label_cell.fill = PatternFill("solid", fgColor=color)
        label_cell.font = Font(name="Aptos", size=9, bold=True, color=WHITE)
        label_cell.alignment = Alignment(horizontal="center", vertical="center")

        value_cell.value = float(value)
        value_cell.number_format = currency_format
        value_cell.fill = PatternFill("solid", fgColor=LIGHT_BLUE)
        value_cell.font = Font(
            name="Aptos Display",
            size=16,
            bold=True,
            color=color,
        )
        value_cell.alignment = Alignment(horizontal="center", vertical="center")

    # ========================================================
    # FEUILLE 1 : TABLEAU DE BORD
    # ========================================================

    if "budget" in data:
        sheet = workbook.create_sheet("Vue d'ensemble")
        configure_sheet(sheet)
        sheet.sheet_properties.tabColor = ORANGE

        style_title(
            sheet,
            "B2:I2",
            "MARVEL | RAPPORT FINANCIER",
        )

        style_subtitle(
            sheet,
            "B3:I3",
            f"Tableau de bord de trésorerie | Généré le "
            f"{generated_at.strftime('%d/%m/%Y à %H:%M')}",
        )

        budget = data["budget"]

        total_donations = Decimal(str(budget.get("total_donations", 0)))
        total_income = Decimal(str(budget.get("total_income", 0)))
        total_expenses = Decimal(str(budget.get("total_expenses", 0)))
        balance = Decimal(str(budget.get("balance", 0)))

        add_kpi(sheet, "B5:C5", "B6:C7", "Dons reçus",
                 total_donations, NAVY)

        add_kpi(sheet, "D5:E5", "D6:E7", "Recettes",
                 total_income, GREEN)

        add_kpi(sheet, "F5:G5", "F6:G7", "Dépenses",
                 total_expenses, ORANGE)

        add_kpi(sheet, "H5:I5", "H6:I7", "Solde disponible",
                 balance, NAVY)

        sheet.row_dimensions[5].height = 24
        sheet.row_dimensions[6].height = 27
        sheet.row_dimensions[7].height = 27

        sheet.merge_cells("B10:I10")
        section = sheet["B10"]
        section.value = "DÉTAIL DU BILAN BUDGÉTAIRE"
        section.fill = PatternFill("solid", fgColor=NAVY)
        section.font = Font(bold=True, color=WHITE, size=11)
        section.alignment = Alignment(vertical="center")
        sheet.row_dimensions[10].height = 28

        indicators = [
            ("Total des dons financiers", total_donations),
            ("Total des recettes", total_income),
            ("Total des dépenses", total_expenses),
            ("Solde disponible", balance),
        ]

        sheet.append([])
        sheet.append(["", "Indicateur financier", "Montant"])

        for cell in sheet[12][1:3]:
            cell.fill = PatternFill("solid", fgColor=LIGHT_BLUE)
            cell.font = Font(bold=True, color=NAVY)
            cell.alignment = Alignment(horizontal="center")

        for label, value in indicators:
            sheet.append(["", label, float(value)])
            row = sheet.max_row

            sheet.cell(row, 2).font = Font(name="Aptos", size=10)
            sheet.cell(row, 3).number_format = currency_format
            sheet.cell(row, 3).font = Font(
                name="Aptos",
                size=10,
                bold=True,
                color=GREEN if label == "Solde disponible" else NAVY,
            )

            for cell in sheet[row][1:3]:
                cell.border = Border(bottom=thin_grey)
                cell.fill = PatternFill(
                    "solid",
                    fgColor=WHITE if row % 2 else LIGHT_GREY,
                )

        sheet.column_dimensions["A"].width = 4
        for column in "BCDEFGHI":
            sheet.column_dimensions[column].width = 17

        sheet.freeze_panes = "B13"
        sheet.print_area = "B2:I16"

    # ========================================================
    # FEUILLE 2 : OPÉRATIONS FINANCIÈRES
    # ========================================================

    if "operations" in data:
        sheet = workbook.create_sheet("Opérations")
        configure_sheet(sheet)
        sheet.sheet_properties.tabColor = NAVY

        style_title(sheet, "A1:F1", "MARVEL | OPÉRATIONS FINANCIÈRES")

        style_subtitle(
            sheet,
            "A2:F2",
            f"Registre des opérations financières | "
            f"Généré le {generated_at.strftime('%d/%m/%Y à %H:%M')}",
        )

        headers = [
            "Identifiant",
            "Montant (DZD)",
            "Catégorie",
            "Date de transaction",
            "Justificatif",
            "Identifiant événement",
        ]

        header_row = 4

        for col, header in enumerate(headers, start=1):
            cell = sheet.cell(header_row, col, header)
            cell.fill = PatternFill("solid", fgColor=NAVY)
            cell.font = Font(bold=True, color=WHITE, size=10)
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )
            cell.border = Border(bottom=Side(style="medium", color=ORANGE))

        sheet.row_dimensions[header_row].height = 34

        for item in data["operations"]:
            transaction_at = item["transaction_at"]

            # Excel ne prend pas en charge les dates avec fuseau horaire.
            if isinstance(transaction_at, datetime) and transaction_at.tzinfo is not None:
                 transaction_at = transaction_at.replace(tzinfo=None)

            row = [
                item["id_fund"],
                float(item["amount"]),
                item["category"] or "Non catégorisé",
                transaction_at,
                item["justificative"] or "Aucun justificatif",
                item["id_event"] or "",
            ]

            sheet.append(row)
            row_number = sheet.max_row

            for cell in sheet[row_number]:
                cell.font = Font(name="Aptos", size=9, color=DARK_GREY)
                cell.alignment = Alignment(
                    vertical="center",
                    wrap_text=True,
                )
                cell.border = Border(bottom=thin_grey)

                if row_number % 2 == 0:
                    cell.fill = PatternFill("solid", fgColor=LIGHT_GREY)

            amount_cell = sheet.cell(row_number, 2)
            amount_cell.number_format = currency_format
            amount_cell.alignment = Alignment(horizontal="right")

            amount_cell.font = Font(
                name="Aptos",
                size=9,
                bold=True,
                color=GREEN if amount_cell.value >= 0 else RED,
            )

            date_cell = sheet.cell(row_number, 4)
            if isinstance(date_cell.value, datetime):
                date_cell.number_format = date_format

            proof_cell = sheet.cell(row_number, 5)
            if isinstance(proof_cell.value, str) and proof_cell.value.startswith("https://"):
                proof_cell.hyperlink = proof_cell.value
                proof_cell.style = "Hyperlink"
                proof_cell.value = "Consulter le justificatif"

            sheet.row_dimensions[row_number].height = 30

        last_row = sheet.max_row

        if last_row > header_row:
            table = Table(
                displayName="TreasuryOperations",
                ref=f"A{header_row}:F{last_row}",
            )

            table.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium2",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False,
            )

            sheet.add_table(table)
        else:
            sheet.auto_filter.ref = f"A{header_row}:F{header_row}"

        widths = {
            "A": 38,
            "B": 19,
            "C": 23,
            "D": 23,
            "E": 48,
            "F": 38,
        }

        for column, width in widths.items():
            sheet.column_dimensions[column].width = width

        sheet.freeze_panes = "A5"
        sheet.sheet_view.zoomScale = 85
        sheet.print_title_rows = "1:4"

    # Garantir qu'un classeur est toujours valide.
    if not workbook.sheetnames:
        sheet = workbook.create_sheet("Rapport")
        sheet["A1"] = "MARVEL | Rapport de trésorerie"
        sheet["A1"].font = Font(size=18, bold=True, color=NAVY)

    workbook.properties.title = "Rapport financier MARVEL"
    workbook.properties.subject = "Bilan et opérations de trésorerie"
    workbook.properties.creator = "MARVEL"

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return output.getvalue()


def generate_pdf(data: dict) -> bytes:
    """Génère un rapport PDF professionnel de la trésorerie MARVEL."""

    output = BytesIO()

    # Identité visuelle
    NAVY = colors.HexColor("#17335A")
    ORANGE = colors.HexColor("#EA580C")
    LIGHT_BLUE = colors.HexColor("#EAF0F7")
    LIGHT_GREY = colors.HexColor("#F4F6F9")
    DARK_GREY = colors.HexColor("#475569")
    GREEN = colors.HexColor("#15803D")
    RED = colors.HexColor("#DC2626")
    WHITE = colors.white

    generated_at = datetime.now()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=38,
        leftMargin=38,
        topMargin=76,
        bottomMargin=48,
        title="Rapport financier MARVEL",
        author="MARVEL",
        subject="Rapport de trésorerie",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "MarvelTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=28,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "MarvelSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        textColor=DARK_GREY,
        alignment=TA_LEFT,
    )

    section_style = ParagraphStyle(
        "MarvelSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=NAVY,
        spaceBefore=12,
        spaceAfter=9,
    )

    normal_style = ParagraphStyle(
        "MarvelNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=DARK_GREY,
    )

    small_style = ParagraphStyle(
        "MarvelSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=DARK_GREY,
        wordWrap="CJK",
    )

    elements = []

    # ========================================================
    # EN-TÊTE DU RAPPORT
    # ========================================================

    elements.append(
        Paragraph(
            "MARVEL",
            ParagraphStyle(
                "Brand",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=ORANGE,
                spaceAfter=8,
            ),
        )
    )

    elements.append(
        Paragraph("Rapport financier de trésorerie", title_style)
    )

    elements.append(
        Paragraph(
            "Suivi des dons, recettes, dépenses et opérations financières",
            subtitle_style,
        )
    )

    elements.append(Spacer(1, 12))

    # Ligne orange de séparation
    separator = PDFTable(
        [[""]],
        colWidths=[765],
        rowHeights=[3],
    )

    separator.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    elements.append(separator)
    elements.append(Spacer(1, 16))

    elements.append(
        Paragraph(
            f"<b>Date de génération :</b> "
            f"{generated_at.strftime('%d/%m/%Y à %H:%M')}",
            normal_style,
        )
    )

    elements.append(Spacer(1, 15))

    # ========================================================
    # SYNTHÈSE BUDGÉTAIRE
    # ========================================================

    if "budget" in data:
        budget = data["budget"]

        total_donations = Decimal(
            str(budget.get("total_donations", 0))
        )
        total_income = Decimal(
            str(budget.get("total_income", 0))
        )
        total_expenses = Decimal(
            str(budget.get("total_expenses", 0))
        )
        balance = Decimal(
            str(budget.get("balance", 0))
        )

        def format_money(value):
            return f"{value:,.2f} DZD".replace(",", " ")

        elements.append(
            Paragraph("Synthèse budgétaire", section_style)
        )

        def kpi_cell(label, value, color):
            label_paragraph = Paragraph(
                f'<font color="#FFFFFF"><b>{label.upper()}</b></font>',
                ParagraphStyle(
                    "KpiLabel",
                    parent=normal_style,
                    alignment=TA_CENTER,
                    fontSize=8,
                ),
            )

            value_paragraph = Paragraph(
                f'<font color="{color}"><b>{format_money(value)}</b></font>',
                ParagraphStyle(
                    "KpiValue",
                    parent=normal_style,
                    alignment=TA_CENTER,
                    fontSize=14,
                    leading=19,
                ),
            )

            return [label_paragraph, value_paragraph]

        kpi_data = [[
            kpi_cell("Dons reçus", total_donations, "#17335A"),
            kpi_cell("Recettes", total_income, "#15803D"),
            kpi_cell("Dépenses", total_expenses, "#EA580C"),
            kpi_cell("Solde disponible", balance, "#17335A"),
        ]]

        kpi_table = PDFTable(
            kpi_data,
            colWidths=[191] * 4,
            rowHeights=[65],
        )

        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#DCE3EC")),
            ("INNERGRID", (0, 0), (-1, -1), 0.7, WHITE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))

        elements.append(kpi_table)
        elements.append(Spacer(1, 18))

        budget_rows = [
            [
                Paragraph("<b>Indicateur financier</b>", normal_style),
                Paragraph("<b>Montant</b>", normal_style),
            ],
            ["Total des dons financiers", format_money(total_donations)],
            ["Total des recettes", format_money(total_income)],
            ["Total des dépenses", format_money(total_expenses)],
            ["Solde disponible", format_money(balance)],
        ]

        budget_table = PDFTable(
            budget_rows,
            colWidths=[500, 264],
            repeatRows=1,
        )

        budget_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE3EC")),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK_GREY),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
            ("TEXTCOLOR", (1, 4), (1, 4), GREEN),
        ]))

        elements.append(budget_table)
        elements.append(Spacer(1, 18))

    # ========================================================
    # TABLEAU DES OPÉRATIONS
    # ========================================================

    if "operations" in data:
        operations = data["operations"]

        elements.append(
            Paragraph(
                "Registre des opérations financières",
                section_style,
            )
        )

        elements.append(
            Paragraph(
                f"Nombre total d'opérations : <b>{len(operations)}</b>",
                normal_style,
            )
        )

        elements.append(Spacer(1, 9))

        headers = [
            "Identifiant",
            "Montant",
            "Catégorie",
            "Date",
            "Justificatif",
            "Événement",
        ]

        table_data = [[
            Paragraph(f"<b>{header}</b>", small_style)
            for header in headers
        ]]

        for item in operations:
            transaction_date = item["transaction_at"]

            if isinstance(transaction_date, datetime):
                transaction_date = transaction_date.strftime(
                    "%d/%m/%Y %H:%M"
                )

            amount = Decimal(str(item["amount"]))

            justification = (
                item["justificative"] or "Aucun justificatif"
            )

            if (
                isinstance(justification, str)
                and justification.startswith("https://")
            ):
                justification = (
                    f'<link href="{justification}" color="#EA580C">'
                    "Consulter le justificatif</link>"
                )

            row = [
                Paragraph(str(item["id_fund"]), small_style),
                Paragraph(
                    f'<font color="{"#DC2626" if amount < 0 else "#15803D"}">'
                    f'<b>{format_money(amount)}</b></font>',
                    ParagraphStyle(
                        "Amount",
                        parent=small_style,
                        alignment=TA_RIGHT,
                    ),
                ),
                Paragraph(
                    str(item["category"] or "Non catégorisé"),
                    small_style,
                ),
                Paragraph(str(transaction_date), small_style),
                Paragraph(str(justification), small_style),
                Paragraph(str(item["id_event"] or "-"), small_style),
            ]

            table_data.append(row)

        operations_table = LongTable(
            table_data,
            colWidths=[112, 85, 100, 100, 200, 167],
            repeatRows=1,
            hAlign="LEFT",
        )

        operations_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE3EC")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        elements.append(operations_table)

    # ========================================================
    # EN-TÊTE ET PIED DE PAGE
    # ========================================================

    def draw_page(canvas, doc):
        canvas.saveState()

        page_width, page_height = landscape(A4)

        # En-tête
        canvas.setFillColor(NAVY)
        canvas.rect(
            0,
            page_height - 42,
            page_width,
            42,
            fill=1,
            stroke=0,
        )

        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(38, page_height - 26, "MARVEL")

        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            page_width - 38,
            page_height - 26,
            "RAPPORT DE TRÉSORERIE",
        )

        # Pied de page
        canvas.setStrokeColor(colors.HexColor("#DCE3EC"))
        canvas.setLineWidth(0.6)
        canvas.line(38, 34, page_width - 38, 34)

        canvas.setFillColor(DARK_GREY)
        canvas.setFont("Helvetica", 7)

        canvas.drawString(
            38,
            21,
            f"Document généré le "
            f"{generated_at.strftime('%d/%m/%Y à %H:%M')}",
        )

        canvas.drawRightString(
            page_width - 38,
            21,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    document.build(
        elements,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )

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