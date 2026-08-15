"""Builds the customer-facing printed quote (quote design.pdf) as HTML for
QTextDocument, replacing the earlier placeholder that just printed a
screenshot of the working UI (edit controls, DigiKey panel, and all)."""

import html
from datetime import datetime

from app import config
from app.cost_model import price_harness, price_quote
from app.models import Quote

_TOKENS = {
    "text": "#1a1917",
    "muted": "#5c5952",
    "label": "#8b887f",
    "rule": "#eaeae7",
    "accent": "#b45309",
}


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _esc(text: str) -> str:
    return html.escape(text or "")


def _today() -> str:
    now = datetime.now()
    return f"{now.day} {now.strftime('%B %Y')}"


def build_quote_html(quote: Quote) -> str:
    rows = [(h, price_harness(h, quote.labor)) for h in quote.harnesses]
    totals = price_quote(quote)

    address_lines = "<br/>".join(_esc(line) for line in config.COMPANY_ADDRESS_LINES)

    bill_to_lines = []
    if quote.customer_attn.strip():
        bill_to_lines.append(f"Attn: {_esc(quote.customer_attn)}")
    bill_to_lines.extend(_esc(line) for line in quote.customer_address.splitlines() if line.strip())
    bill_to_html = "<br/>".join(bill_to_lines)

    item_rows = "".join(
        f"""
        <tr>
            <td style="padding:8px 8px 8px 0;">{_esc(h.name)}</td>
            <td style="padding:8px 8px;">{_esc(h.part_no) or '—'}</td>
            <td align="right" style="padding:8px 8px;">{pricing.qty}</td>
            <td style="padding:8px 8px;">EA</td>
            <td align="right" style="padding:8px 8px;">{_money(pricing.unit_price)}</td>
            <td align="right" style="padding:8px 0 8px 8px;">{_money(pricing.extended)}</td>
        </tr>
        """
        for h, pricing in rows
    )

    return f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                 font-size: 10pt; color: {_TOKENS['text']};">

    <table width="100%" cellspacing="0" style="border-bottom: 2px solid {_TOKENS['text']};
                                                 padding-bottom: 14px;">
        <tr>
            <td style="vertical-align: top;">
                <div style="font-size: 19pt; font-weight: bold;">{_esc(config.COMPANY_NAME)}</div>
                <div style="color:{_TOKENS['muted']}; font-size: 9pt; margin-top: 8px; line-height: 1.5;">
                    {address_lines}<br/>
                    {_esc(config.COMPANY_PHONE)} &middot; {_esc(config.COMPANY_EMAIL)}
                </div>
            </td>
            <td style="vertical-align: top; text-align: right;">
                <div style="font-size: 15pt; font-weight: bold; color: {_TOKENS['accent']};">QUOTATION</div>
                <table style="margin-left: auto; margin-top: 10px;" cellspacing="0">
                    <tr>
                        <td style="color:{_TOKENS['muted']}; text-align:right; padding-right:10px;">Quote no.</td>
                        <td style="font-weight:bold; text-align:right;">{_esc(config.QUOTE_NUMBER)}</td>
                    </tr>
                    <tr>
                        <td style="color:{_TOKENS['muted']}; text-align:right; padding-right:10px;">Revision</td>
                        <td style="text-align:right;">{_esc(config.QUOTE_REVISION)}</td>
                    </tr>
                    <tr>
                        <td style="color:{_TOKENS['muted']}; text-align:right; padding-right:10px;">Date</td>
                        <td style="text-align:right;">{_today()}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <div style="margin-top: 24px; color:{_TOKENS['label']}; font-size: 8pt; letter-spacing: 1px;">
        QUOTATION FOR
    </div>
    <div style="font-size: 13pt; font-weight: bold; margin-top: 3px;">{_esc(quote.customer) or '—'}</div>
    <div style="color:{_TOKENS['muted']}; font-size: 9.5pt; margin-top: 4px; line-height: 1.5;">
        {bill_to_html}
    </div>

    <table width="100%" cellspacing="0" style="margin-top: 28px; border-collapse: collapse;">
        <tr style="border-bottom: 1px solid {_TOKENS['text']};">
            <th align="left" style="color:{_TOKENS['label']}; font-size:8pt; padding:0 8px 8px 0;">HARNESS</th>
            <th align="left" style="color:{_TOKENS['label']}; font-size:8pt; padding:0 8px 8px;">PART NUMBER</th>
            <th align="right" style="color:{_TOKENS['label']}; font-size:8pt; padding:0 8px 8px;">QTY</th>
            <th align="left" style="color:{_TOKENS['label']}; font-size:8pt; padding:0 8px 8px;">U/M</th>
            <th align="right" style="color:{_TOKENS['label']}; font-size:8pt; padding:0 8px 8px;">PRICE</th>
            <th align="right" style="color:{_TOKENS['label']}; font-size:8pt; padding:0 0 8px 8px;">EXTENDED</th>
        </tr>
        {item_rows}
        <tr>
            <td colspan="6" style="border-bottom: 2px solid {_TOKENS['text']}; padding:0;"></td>
        </tr>
        <tr>
            <td colspan="4"></td>
            <td align="right" style="font-weight:bold; padding-top:10px;">Subtotal</td>
            <td align="right" style="font-weight:bold; font-size:12pt; padding-top:10px;">{_money(totals.quote_price)}</td>
        </tr>
    </table>

    <table width="100%" style="margin-top: 90px; border-top: 1px solid {_TOKENS['rule']}; padding-top: 14px;">
        <tr>
            <td style="width: 74%; vertical-align: top; font-size: 8pt; color:{_TOKENS['muted']}; line-height: 1.5;">
                <b>Terms.</b> {_esc(config.QUOTE_TERMS)}
            </td>
            <td style="vertical-align: top; text-align: right; font-size: 9pt;">
                <b>{_esc(config.QUOTE_NUMBER)}</b><br/>Rev {_esc(config.QUOTE_REVISION)}
            </td>
        </tr>
    </table>

    </body>
    </html>
    """
