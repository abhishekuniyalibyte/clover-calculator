"""
Blockpay Proposal PDF Generator
Generates a branded, professional proposal PDF from an Analysis object.

Usage:
    generator = ProposalPDFGenerator(analysis, request)
    pdf_buffer = generator.generate()   # returns BytesIO
"""

import os
from datetime import date
from io import BytesIO

from django.conf import settings
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .calculators import AnalysisCalculator

# ── Brand colours ──────────────────────────────────────────────────────────────
NAVY        = HexColor('#1B3A6B')
LIGHT_NAVY  = HexColor('#2C5F9E')
NAVY_LIGHT  = HexColor('#EFF6FF')   # very pale blue background
WHITE       = HexColor('#FFFFFF')
BLACK       = HexColor('#000000')
LIGHT_GRAY  = HexColor('#F5F7FA')
MID_GRAY    = HexColor('#9CA3AF')
BORDER_GRAY = HexColor('#E5E7EB')
GREEN       = HexColor('#16A34A')
RED         = HexColor('#DC2626')


class ProposalPDFGenerator:
    """Generates a branded Blockpay proposal PDF from an Analysis object."""

    PAGE_W, PAGE_H = letter
    MARGIN = 0.70 * inch

    def __init__(self, analysis, request=None):
        self.analysis = analysis
        self.request = request
        self.calculator = AnalysisCalculator(analysis)
        self.current  = self.calculator.calculate_current_costs()
        self.proposed = self.calculator.calculate_proposed_costs()
        self.onetime  = self.calculator.calculate_onetime_costs()
        self.savings  = self.calculator.calculate_savings(
            self.current['total_monthly'],
            self.proposed['total_monthly'],
            self.onetime['total'],
        )
        self.selected_pricing = self.calculator.selected_pricing
        self._styles = self._build_styles()

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(amount):
        if amount is None:
            return '$0.00'
        return f'${float(amount):,.2f}'

    def _content_w(self):
        return self.PAGE_W - 2 * self.MARGIN

    def _logo_path(self, filename):
        """Return absolute path to media/brand/<filename> if the file exists."""
        path = os.path.join(settings.MEDIA_ROOT, 'brand', filename)
        return path if os.path.exists(path) else None

    def _media_abs(self, field_file):
        """Convert a Django FileField value to an absolute filesystem path."""
        if not field_file:
            return None
        try:
            path = os.path.join(settings.MEDIA_ROOT, str(field_file))
            return path if os.path.exists(path) else None
        except Exception:
            return None

    # ── Style sheet ───────────────────────────────────────────────────────────

    def _build_styles(self):
        s = {}

        def ps(name, **kw):
            return ParagraphStyle(name, **kw)

        s['title']     = ps('title',     fontName='Helvetica-Bold',  fontSize=20, textColor=WHITE,       alignment=TA_CENTER, spaceAfter=2)
        s['subtitle']  = ps('subtitle',  fontName='Helvetica',       fontSize=10, textColor=HexColor('#B8CCE4'), alignment=TA_CENTER)
        s['section']   = ps('section',   fontName='Helvetica-Bold',  fontSize=12, textColor=NAVY,        spaceBefore=14, spaceAfter=5)
        s['body']      = ps('body',      fontName='Helvetica',       fontSize=10, textColor=BLACK,       spaceAfter=3)
        s['small']     = ps('small',     fontName='Helvetica',       fontSize=8,  textColor=MID_GRAY)
        s['bold']      = ps('bold',      fontName='Helvetica-Bold',  fontSize=10, textColor=BLACK)
        s['th']        = ps('th',        fontName='Helvetica-Bold',  fontSize=9,  textColor=WHITE,       alignment=TA_CENTER)
        s['td_right']  = ps('td_right',  fontName='Helvetica',       fontSize=10, textColor=BLACK,       alignment=TA_RIGHT)
        s['td_right_b']= ps('td_right_b',fontName='Helvetica-Bold',  fontSize=10, textColor=WHITE,       alignment=TA_RIGHT)
        s['td_left_b'] = ps('td_left_b', fontName='Helvetica-Bold',  fontSize=10, textColor=WHITE)
        s['hero_lbl']  = ps('hero_lbl',  fontName='Helvetica-Bold',  fontSize=8,  textColor=MID_GRAY,    alignment=TA_CENTER)
        s['hero_curr'] = ps('hero_curr', fontName='Helvetica-Bold',  fontSize=22, textColor=RED,         alignment=TA_CENTER)
        s['hero_prop'] = ps('hero_prop', fontName='Helvetica-Bold',  fontSize=22, textColor=GREEN,       alignment=TA_CENTER)
        s['hero_save'] = ps('hero_save', fontName='Helvetica-Bold',  fontSize=24, textColor=WHITE,       alignment=TA_CENTER)
        s['hero_tag']  = ps('hero_tag',  fontName='Helvetica-Bold',  fontSize=9,  textColor=HexColor('#BBF7D0'), alignment=TA_CENTER)
        s['hero_sub']  = ps('hero_sub',  fontName='Helvetica',       fontSize=8,  textColor=MID_GRAY,    alignment=TA_CENTER)
        s['tl_val']    = ps('tl_val',    fontName='Helvetica-Bold',  fontSize=12, textColor=NAVY,        alignment=TA_CENTER)
        s['footer']    = ps('footer',    fontName='Helvetica',       fontSize=8,  textColor=MID_GRAY,    alignment=TA_CENTER)
        s['prep']      = ps('prep',      fontName='Helvetica-Bold',  fontSize=8,  textColor=MID_GRAY)
        s['biz']       = ps('biz',       fontName='Helvetica-Bold',  fontSize=15, textColor=NAVY,        spaceAfter=2)
        s['addr']      = ps('addr',      fontName='Helvetica',       fontSize=9,  textColor=HexColor('#374151'))
        s['curr_proc'] = ps('curr_proc', fontName='Helvetica-Bold',  fontSize=8,  textColor=MID_GRAY,    alignment=TA_RIGHT)
        s['comp_name'] = ps('comp_name', fontName='Helvetica-Bold',  fontSize=15, textColor=HexColor('#374151'), alignment=TA_RIGHT)
        s['comp_cost'] = ps('comp_cost', fontName='Helvetica-Bold',  fontSize=10, textColor=RED,         alignment=TA_RIGHT, spaceBefore=3)

        return s

    # ── Page footer callback ───────────────────────────────────────────────────

    def _add_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawCentredString(
            self.PAGE_W / 2.0, 0.38 * inch,
            'Confidential — Prepared by Blockpay  |  Powered by Clover'
        )
        canvas.drawRightString(
            self.PAGE_W - self.MARGIN, 0.38 * inch,
            f'Page {doc.page}'
        )
        canvas.restoreState()

    # ── Public entry point ────────────────────────────────────────────────────

    def generate(self):
        """Build and return the proposal PDF as a BytesIO buffer."""
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=self.MARGIN,
            rightMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=0.65 * inch,
            title=f"Blockpay Proposal — {self.analysis.merchant.business_name}",
        )

        story = []
        story += self._section_header()
        story += self._section_merchant_competitor()
        story += self._section_savings_hero()
        story += self._section_current_costs()
        story += self._section_proposed_solution()
        if self.onetime['total'] > 0:
            story += self._section_onetime_fees()
        story += self._section_savings_timeline()

        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        buf.seek(0)
        return buf

    # ── Section builders ──────────────────────────────────────────────────────

    def _section_header(self):
        """Navy header bar with Blockpay logo | PROPOSAL title | Clover logo."""
        cw = self._content_w()
        logo_h = 0.45 * inch

        bp_path = self._logo_path('blockpay_logo.png')
        cl_path = self._logo_path('clover_logo.png')

        left_cell  = Image(bp_path, width=1.6 * inch, height=logo_h) if bp_path \
                     else Paragraph('BLOCKPAY', ParagraphStyle('_bl', fontName='Helvetica-Bold', fontSize=13, textColor=WHITE))
        right_cell = Image(cl_path, width=1.4 * inch, height=logo_h) if cl_path \
                     else Paragraph('CLOVER', ParagraphStyle('_cl', fontName='Helvetica-Bold', fontSize=13, textColor=HexColor('#00A651'), alignment=TA_RIGHT))

        mid_cell = [
            Paragraph('PROPOSAL', self._styles['title']),
            Paragraph('Payment Processing Analysis', self._styles['subtitle']),
        ]

        col_w = [1.7 * inch, cw - 3.4 * inch, 1.7 * inch]
        header_tbl = Table([[left_cell, mid_cell, right_cell]], colWidths=col_w, rowHeights=[0.85 * inch])
        header_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), NAVY),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',         (0, 0), (0,  0),  'LEFT'),
            ('ALIGN',         (2, 0), (2,  0),  'RIGHT'),
            ('LEFTPADDING',   (0, 0), (0,  0),  10),
            ('RIGHTPADDING',  (2, 0), (2,  0),  10),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        date_para = Paragraph(
            f'Generated: {date.today().strftime("%B %d, %Y")}',
            ParagraphStyle('_dt', fontName='Helvetica', fontSize=8, textColor=MID_GRAY, spaceAfter=10)
        )

        return [header_tbl, Spacer(1, 0.04 * inch), date_para]

    def _section_merchant_competitor(self):
        """Prepared-for merchant info on the left; current processor on the right."""
        cw = self._content_w()
        merchant    = self.analysis.merchant
        competitor  = self.analysis.competitor

        # Left column
        left = [
            Paragraph('PREPARED FOR', self._styles['prep']),
            Paragraph(merchant.business_name, self._styles['biz']),
        ]
        if merchant.business_address:
            left.append(Paragraph(merchant.business_address, self._styles['addr']))

        # Right column
        right = []
        if competitor:
            right.append(Paragraph('CURRENT PROCESSOR', self._styles['curr_proc']))
            comp_logo = self._media_abs(competitor.logo)
            if comp_logo:
                right.append(Image(comp_logo, width=1.1 * inch, height=0.35 * inch))
            else:
                right.append(Paragraph(competitor.name, self._styles['comp_name']))
            right.append(Paragraph(
                f'Monthly Cost: {self._fmt(self.current["total_monthly"])}',
                self._styles['comp_cost']
            ))

        info_tbl = Table([[left, right]], colWidths=[cw * 0.56, cw * 0.44])
        info_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), LIGHT_GRAY),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING',   (0, 0), (0,  0),  12),
            ('RIGHTPADDING',  (1, 0), (1,  0),  12),
            ('LINEBELOW',     (0, 0), (-1, -1), 1, BORDER_GRAY),
        ]))

        return [info_tbl, Spacer(1, 0.12 * inch)]

    def _section_savings_hero(self):
        """Three-column savings callout: Current | YOU SAVE | Proposed."""
        cw  = self._content_w()
        col = cw / 3

        current_cells = [
            Paragraph('CURRENT MONTHLY',     self._styles['hero_lbl']),
            Paragraph(self._fmt(self.current['total_monthly']), self._styles['hero_curr']),
            Paragraph('with current processor', self._styles['hero_sub']),
        ]
        savings_cells = [
            Paragraph('YOU SAVE',            ParagraphStyle('_ys', fontName='Helvetica-Bold', fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(self._fmt(self.savings['monthly']), self._styles['hero_save']),
            Paragraph('PER MONTH',           self._styles['hero_tag']),
            Paragraph(f'{self.savings["percent"]:.1f}% reduction', ParagraphStyle('_pct', fontName='Helvetica', fontSize=9, textColor=HexColor('#D1FAE5'), alignment=TA_CENTER)),
        ]
        proposed_cells = [
            Paragraph('BLOCKPAY MONTHLY',    self._styles['hero_lbl']),
            Paragraph(self._fmt(self.proposed['total_monthly']), self._styles['hero_prop']),
            Paragraph('with Blockpay + Clover', self._styles['hero_sub']),
        ]

        hero_tbl = Table(
            [[current_cells, savings_cells, proposed_cells]],
            colWidths=[col, col, col],
            rowHeights=[1.05 * inch],
        )
        hero_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (0, 0), LIGHT_GRAY),
            ('BACKGROUND',    (1, 0), (1, 0), NAVY),
            ('BACKGROUND',    (2, 0), (2, 0), LIGHT_GRAY),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE',     (0, 0), (-1, -1), 2, NAVY),
            ('LINEBELOW',     (0, 0), (-1, -1), 2, NAVY),
        ]))

        yearly_para = Paragraph(
            f'Annual Savings: <b>{self._fmt(self.savings["yearly"])}</b>'
            f'&nbsp;&nbsp;|&nbsp;&nbsp;'
            f'Break-even on one-time costs: <b>{self.savings["break_even_months"]} months</b>',
            ParagraphStyle('_yr', fontName='Helvetica', fontSize=9, textColor=NAVY,
                           alignment=TA_CENTER, spaceBefore=5, spaceAfter=12,
                           backColor=NAVY_LIGHT, borderPad=5)
        )

        return [
            Paragraph('SAVINGS SUMMARY', self._styles['section']),
            hero_tbl,
            yearly_para,
        ]

    def _section_current_costs(self):
        """Table: current processing cost breakdown."""
        cw = self._content_w()
        c  = self.current

        rows = [
            ('Processing Fees',        c['processing_cost']),
            ('Per-Transaction Fees',   c['per_transaction_cost']),
            ('Fixed Monthly Fees',     c['monthly_fees']),
            ('Hardware / Software',    c['hardware_monthly']),
        ]

        data = [[Paragraph('Cost Component', self._styles['th']),
                 Paragraph('Monthly Amount', self._styles['th'])]]

        for label, amount in rows:
            if amount > 0:
                data.append([
                    Paragraph(label, self._styles['body']),
                    Paragraph(self._fmt(amount), self._styles['td_right']),
                ])

        data.append([
            Paragraph('<b>TOTAL CURRENT MONTHLY</b>', self._styles['td_left_b']),
            Paragraph(f'<b>{self._fmt(c["total_monthly"])}</b>', self._styles['td_right_b']),
        ])

        tbl = Table(data, colWidths=[cw * 0.65, cw * 0.35])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1,  0), NAVY),
            ('BACKGROUND',    (0, -1), (-1, -1), RED),
            ('ROWBACKGROUNDS',(0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
            ('GRID',          (0, 0), (-1, -1), 0.4, BORDER_GRAY),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING',   (0, 0), (0, -1),  10),
            ('RIGHTPADDING',  (1, 0), (1, -1),  10),
        ]))

        return [Paragraph('CURRENT PROCESSING COSTS', self._styles['section']), tbl, Spacer(1, 0.1 * inch)]

    def _section_proposed_solution(self):
        """Table: Blockpay proposed cost breakdown (pricing + devices + SaaS)."""
        cw = self._content_w()
        p  = self.proposed

        if self.selected_pricing:
            model_label = Paragraph(
                f'<b>Pricing Model:</b> {self.selected_pricing.get_model_type_display()}',
                self._styles['body']
            )
        else:
            model_label = Spacer(1, 0)

        data = [[
            Paragraph('Component',      self._styles['th']),
            Paragraph('Details',        self._styles['th']),
            Paragraph('Monthly Amount', self._styles['th']),
        ]]

        # Processing
        data.append([
            Paragraph('Processing Fees', self._styles['body']),
            Paragraph(self.selected_pricing.get_model_type_display() if self.selected_pricing else '—', self._styles['small']),
            Paragraph(self._fmt(p['processing_cost']), self._styles['td_right']),
        ])

        # Device leases
        for pd in self.analysis.proposed_devices.select_related('device').all():
            if pd.pricing_type == 'LEASE':
                data.append([
                    Paragraph(pd.device.name, self._styles['body']),
                    Paragraph(f'× {pd.quantity}  (Lease)', self._styles['small']),
                    Paragraph(self._fmt(pd.total_cost), self._styles['td_right']),
                ])

        # SaaS plans
        for ps in self.analysis.proposed_saas.select_related('saas_plan').all():
            data.append([
                Paragraph(ps.saas_plan.plan_name, self._styles['body']),
                Paragraph(f'× {ps.quantity}  (SaaS)', self._styles['small']),
                Paragraph(self._fmt(ps.monthly_cost), self._styles['td_right']),
            ])

        data.append([
            Paragraph('<b>TOTAL BLOCKPAY MONTHLY</b>', self._styles['td_left_b']),
            Paragraph('', self._styles['body']),
            Paragraph(f'<b>{self._fmt(p["total_monthly"])}</b>', self._styles['td_right_b']),
        ])

        tbl = Table(data, colWidths=[cw * 0.44, cw * 0.26, cw * 0.30])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1,  0), NAVY),
            ('BACKGROUND',    (0, -1), (-1, -1), GREEN),
            ('ROWBACKGROUNDS',(0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
            ('GRID',          (0, 0), (-1, -1), 0.4, BORDER_GRAY),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING',   (0, 0), (0, -1),  10),
            ('RIGHTPADDING',  (2, 0), (2, -1),  10),
        ]))

        return [
            Paragraph('PROPOSED BLOCKPAY SOLUTION', self._styles['section']),
            model_label,
            tbl,
            Spacer(1, 0.1 * inch),
        ]

    def _section_onetime_fees(self):
        """Table: one-time fees and device purchases."""
        cw = self._content_w()

        data = [[
            Paragraph('Fee / Item',     self._styles['th']),
            Paragraph('Type',           self._styles['th']),
            Paragraph('Amount',         self._styles['th']),
        ]]

        # Device purchases
        for pd in self.analysis.proposed_devices.select_related('device').all():
            if pd.pricing_type == 'PURCHASE':
                data.append([
                    Paragraph(f'{pd.device.name} × {pd.quantity}', self._styles['body']),
                    Paragraph('Device Purchase', self._styles['small']),
                    Paragraph(self._fmt(pd.total_cost), self._styles['td_right']),
                ])

        # One-time fees
        for fee in self.analysis.onetime_fees.all():
            name = fee.fee_name + (' (Optional)' if fee.is_optional else '')
            data.append([
                Paragraph(name, self._styles['body']),
                Paragraph(fee.get_fee_type_display(), self._styles['small']),
                Paragraph(self._fmt(fee.amount), self._styles['td_right']),
            ])

        data.append([
            Paragraph('<b>TOTAL ONE-TIME</b>', self._styles['td_left_b']),
            Paragraph('', self._styles['body']),
            Paragraph(f'<b>{self._fmt(self.onetime["total"])}</b>', self._styles['td_right_b']),
        ])

        tbl = Table(data, colWidths=[cw * 0.50, cw * 0.25, cw * 0.25])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1,  0), NAVY),
            ('BACKGROUND',    (0, -1), (-1, -1), LIGHT_NAVY),
            ('ROWBACKGROUNDS',(0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
            ('GRID',          (0, 0), (-1, -1), 0.4, BORDER_GRAY),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING',   (0, 0), (0, -1),  10),
            ('RIGHTPADDING',  (2, 0), (2, -1),  10),
        ]))

        return [Paragraph('ONE-TIME COSTS', self._styles['section']), tbl, Spacer(1, 0.1 * inch)]

    def _section_savings_timeline(self):
        """Five-column savings timeline table: Daily → Yearly."""
        cw = self._content_w()
        s  = self.savings

        periods = [
            ('Daily',     s['daily']),
            ('Weekly',    s['weekly']),
            ('Monthly',   s['monthly']),
            ('Quarterly', s['quarterly']),
            ('Yearly',    s['yearly']),
        ]

        col_w = cw / len(periods)

        header_row = [
            Paragraph(label, self._styles['th'])
            for label, _ in periods
        ]
        value_row = [
            Paragraph(self._fmt(val), self._styles['tl_val'])
            for _, val in periods
        ]

        tbl = Table(
            [header_row, value_row],
            colWidths=[col_w] * len(periods),
            rowHeights=[0.3 * inch, 0.45 * inch],
        )
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('BACKGROUND', (0, 1), (-1, 1), NAVY_LIGHT),
            ('GRID',       (0, 0), (-1, -1), 0.4, BORDER_GRAY),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW',  (0, 1), (-1, 1), 2, NAVY),
        ]))

        be_note = Paragraph(
            f'Break-even on one-time costs: <b>{s["break_even_months"]} months</b>',
            ParagraphStyle('_be', fontName='Helvetica', fontSize=9, textColor=MID_GRAY,
                           alignment=TA_CENTER, spaceBefore=5)
        )

        return [
            Paragraph('SAVINGS TIMELINE', self._styles['section']),
            tbl,
            be_note,
            Spacer(1, 0.25 * inch),
        ]
