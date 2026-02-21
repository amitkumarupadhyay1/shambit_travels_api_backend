"""
Voucher PDF Generation Service
Generates travel vouchers for confirmed bookings
"""

import io
import logging
from typing import BinaryIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


class VoucherService:
    """Service for generating booking vouchers as PDF"""

    @staticmethod
    def generate_qr_code(data: str) -> BinaryIO:
        """Generate QR code for booking reference"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_voucher(booking) -> bytes:
        """
        Generate PDF voucher for a booking

        Args:
            booking: Booking instance

        Returns:
            bytes: PDF file content
        """
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Container for PDF elements
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#FF9933"),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#0F2027"),
            spaceAfter=10,
            spaceBefore=15,
            fontName="Helvetica-Bold",
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#1A1A1A"),
            spaceAfter=6,
        )

        small_style = ParagraphStyle(
            "CustomSmall",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#666666"),
            spaceAfter=4,
        )

        # Header with branding
        elements.append(Paragraph("ShamBit", title_style))
        elements.append(Paragraph("A Bit of Goodness in Every Deal", small_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Voucher title
        elements.append(Paragraph("TRAVEL VOUCHER", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Booking reference and QR code
        booking_ref = booking.booking_reference or f"BK{booking.id}"

        # Create QR code
        qr_buffer = VoucherService.generate_qr_code(booking_ref)
        qr_image = Image(qr_buffer, width=1.5 * inch, height=1.5 * inch)

        # Booking info table with QR code
        booking_info_data = [
            [
                Paragraph(f"<b>Booking Reference:</b> {booking_ref}", normal_style),
                qr_image,
            ],
            [
                Paragraph(
                    f"<b>Booking Date:</b> {booking.created_at.strftime('%d %B %Y')}",
                    normal_style,
                ),
                "",
            ],
            [
                Paragraph(
                    f"<b>Status:</b> {booking.get_status_display()}", normal_style
                ),
                "",
            ],
        ]

        booking_info_table = Table(booking_info_data, colWidths=[4 * inch, 2 * inch])
        booking_info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("SPAN", (1, 0), (1, 2)),
                ]
            )
        )

        elements.append(booking_info_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Customer details
        elements.append(Paragraph("Customer Information", heading_style))
        customer_data = [
            ["Name:", booking.customer_name],
            ["Email:", booking.customer_email],
            ["Phone:", booking.customer_phone],
        ]

        customer_table = Table(customer_data, colWidths=[1.5 * inch, 4.5 * inch])
        customer_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A1A1A")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(customer_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Package details
        elements.append(Paragraph("Package Details", heading_style))
        package_data = [
            ["Package:", booking.package.name],
            ["Destination:", booking.package.city.name],
            ["Travel Date:", booking.booking_date.strftime("%d %B %Y")],
            ["Number of Travelers:", str(booking.num_travelers)],
        ]

        package_table = Table(package_data, colWidths=[1.5 * inch, 4.5 * inch])
        package_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A1A1A")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(package_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Traveler details
        if booking.traveler_details:
            elements.append(Paragraph("Traveler Details", heading_style))
            traveler_data = [["#", "Name", "Age", "Gender"]]

            for idx, traveler in enumerate(booking.traveler_details, 1):
                traveler_data.append(
                    [
                        str(idx),
                        traveler.get("name", "N/A"),
                        str(traveler.get("age", "N/A")),
                        traveler.get("gender", "N/A"),
                    ]
                )

            traveler_table = Table(
                traveler_data, colWidths=[0.5 * inch, 2.5 * inch, 1 * inch, 1.5 * inch]
            )
            traveler_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF9933")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#FFF5E6")],
                        ),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )

            elements.append(traveler_table)
            elements.append(Spacer(1, 0.3 * inch))

        # Selected components
        elements.append(Paragraph("Itinerary Components", heading_style))

        # Experiences
        if booking.selected_experiences.exists():
            elements.append(Paragraph("<b>Experiences:</b>", normal_style))
            for exp in booking.selected_experiences.all():
                elements.append(Paragraph(f"• {exp.name}", normal_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Hotel
        elements.append(
            Paragraph(
                f"<b>Accommodation:</b> {booking.selected_hotel_tier.name}",
                normal_style,
            )
        )
        elements.append(Spacer(1, 0.1 * inch))

        # Transport
        elements.append(
            Paragraph(
                f"<b>Transport:</b> {booking.selected_transport.name}", normal_style
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # Price breakdown
        elements.append(Paragraph("Price Breakdown", heading_style))

        price_data = [
            ["Description", "Amount"],
            ["Per Person Price", f"₹{float(booking.total_price):,.2f}"],
            ["Number of Travelers", str(booking.num_travelers)],
        ]

        # Add chargeable travelers if different
        chargeable_count = booking.get_chargeable_travelers_count()
        if chargeable_count != booking.num_travelers:
            price_data.append(["Chargeable Travelers", str(chargeable_count)])

        # Total amount
        total_amount = booking.total_amount_paid or (
            float(booking.total_price) * chargeable_count
        )
        price_data.append(["Total Amount Paid", f"₹{float(total_amount):,.2f}"])

        price_table = Table(price_data, colWidths=[4 * inch, 2 * inch])
        price_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2027")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -2),
                        [colors.white, colors.HexColor("#FFF5E6")],
                    ),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FFF5E6")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(price_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Special requests
        if booking.special_requests:
            elements.append(Paragraph("Special Requests", heading_style))
            elements.append(Paragraph(booking.special_requests, normal_style))
            elements.append(Spacer(1, 0.3 * inch))

        # Important information
        elements.append(Paragraph("Important Information", heading_style))
        important_info = [
            "• Please carry a valid photo ID proof during your travel",
            ("• Reach the pickup point 15 minutes before the " "scheduled time"),
            "• This voucher must be presented at the time of service",
            (
                "• For any changes or cancellations, please contact us "
                "at least 48 hours in advance"
            ),
            "• Emergency contact: +91 9005457111",
        ]

        for info in important_info:
            elements.append(Paragraph(info, normal_style))

        elements.append(Spacer(1, 0.3 * inch))

        # Terms and conditions
        elements.append(Paragraph("Terms & Conditions", heading_style))
        terms = [
            "• All bookings are subject to availability",
            "• Cancellation charges apply as per our refund policy",
            (
                "• The company reserves the right to modify the itinerary "
                "due to unforeseen circumstances"
            ),
            "• Travel insurance is recommended but not included",
            ("• Please refer to our website for complete terms and " "conditions"),
        ]

        for term in terms:
            elements.append(Paragraph(term, small_style))

        elements.append(Spacer(1, 0.4 * inch))

        # Footer
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
        )

        elements.append(Paragraph("Thank you for choosing ShamBit!", footer_style))
        elements.append(
            Paragraph("For support: support@shambit.com | +91 9005457111", footer_style)
        )
        elements.append(Paragraph("www.shambit.com", footer_style))

        # Build PDF
        doc.build(elements)

        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()

        logger.info(f"Voucher generated for booking {booking.id} ({booking_ref})")

        return pdf_content
