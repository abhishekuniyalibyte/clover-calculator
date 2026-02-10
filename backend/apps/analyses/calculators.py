from decimal import Decimal, ROUND_HALF_UP


ZERO = Decimal('0.00')

# Blockpay base pricing defaults (from Pricing Logic doc)
DEFAULT_COST_PLUS_MARKUP = Decimal('0.10')        # 0.10% on credit volume
DEFAULT_COST_PLUS_CARD_BRAND = Decimal('0.15')    # 0.15% on credit volume
DEFAULT_IPLUS_MARKUP = Decimal('0.25')            # 0.25% bundled on credit volume
DEFAULT_VISA_RATE = Decimal('1.36')               # 1.36% on Visa volume
DEFAULT_MC_RATE = Decimal('1.38')                 # 1.38% on MC volume
DEFAULT_AMEX_RATE = Decimal('2.65')               # 2.65% on Amex volume
DEFAULT_BILLBACK_RATE = Decimal('0.25')           # 0.25% on non-qualified volume
DEFAULT_INTERAC_FEE = Decimal('0.04')             # $0.04 per Interac transaction


def to_decimal(value):
    """Convert a value to Decimal safely, return ZERO if None."""
    if value is None:
        return ZERO
    return Decimal(str(value))


def q(value):
    """Quantize to 2 decimal places."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class AnalysisCalculator:
    """
    Service class that computes cost comparison between a merchant's current
    processor costs and the proposed Blockpay solution for a given Analysis.

    Supports all 4 Blockpay pricing models:
      - Cost Plus  : interchange pass-through + card brand fee + markup + Interac per-item
      - iPlus      : interchange pass-through + bundled markup + Interac per-item
      - Discount Rate (Billback) : per-brand rates + billback on non-qualified + Interac per-item
      - Surcharge Program : cardholder pays surcharge; merchant billed program discount on total ticket

    Usage:
        calculator = AnalysisCalculator(analysis)
        report = calculator.get_full_report()
    """

    def __init__(self, analysis):
        self.analysis = analysis
        self._hardware = None
        self._selected_pricing = None
        self._proposed_devices = None
        self._proposed_saas = None
        self._onetime_fees = None

    # -------------------------------------------------------------------------
    # Lazy-loaded related data
    # -------------------------------------------------------------------------

    @property
    def hardware(self):
        if self._hardware is None:
            self._hardware = list(self.analysis.hardware_costs.all())
        return self._hardware

    @property
    def selected_pricing(self):
        if self._selected_pricing is None:
            qs = self.analysis.pricing_models.all()
            self._selected_pricing = qs.filter(is_selected=True).first() or qs.first()
        return self._selected_pricing

    @property
    def proposed_devices(self):
        if self._proposed_devices is None:
            self._proposed_devices = list(self.analysis.proposed_devices.all())
        return self._proposed_devices

    @property
    def proposed_saas(self):
        if self._proposed_saas is None:
            self._proposed_saas = list(self.analysis.proposed_saas.all())
        return self._proposed_saas

    @property
    def onetime_fees(self):
        if self._onetime_fees is None:
            self._onetime_fees = list(self.analysis.onetime_fees.all())
        return self._onetime_fees

    # -------------------------------------------------------------------------
    # Current Costs
    # -------------------------------------------------------------------------

    def calculate_current_costs(self):
        """
        Compute what the merchant currently pays their processor each month.
        Uses the all-in effective processing rate from the Analysis fields.
        """
        a = self.analysis
        monthly_volume = to_decimal(a.monthly_volume)
        txn_count = to_decimal(a.monthly_transaction_count)

        # Processing cost: volume × effective rate (includes interchange + markup + brand fees)
        processing_cost = ZERO
        if a.current_processing_rate is not None and monthly_volume > ZERO:
            processing_cost = q(
                monthly_volume * to_decimal(a.current_processing_rate) / Decimal('100')
            )

        # Per-transaction fees (auth fees, per-item charges)
        per_transaction_cost = ZERO
        if a.current_transaction_fees is not None and txn_count > ZERO:
            per_transaction_cost = q(txn_count * to_decimal(a.current_transaction_fees))

        # Fixed monthly fees from statement
        monthly_fees = to_decimal(a.current_monthly_fees)

        # Existing hardware monthly recurring costs
        hardware_monthly = ZERO
        for hw in self.hardware:
            if hw.cost_type in ('MONTHLY_LEASE', 'MONTHLY_SUBSCRIPTION'):
                hardware_monthly += to_decimal(hw.amount) * to_decimal(hw.quantity)
        hardware_monthly = q(hardware_monthly)

        total_monthly = processing_cost + per_transaction_cost + monthly_fees + hardware_monthly

        return {
            'processing_cost': float(processing_cost),
            'per_transaction_cost': float(per_transaction_cost),
            'monthly_fees': float(monthly_fees),
            'hardware_monthly': float(hardware_monthly),
            'total_monthly': float(total_monthly),
        }

    # -------------------------------------------------------------------------
    # Proposed Costs
    # -------------------------------------------------------------------------

    def calculate_proposed_costs(self):
        """
        Compute the total monthly cost under the Blockpay proposal.
        Applies the correct formula for each pricing model.
        """
        a = self.analysis
        monthly_volume = to_decimal(a.monthly_volume)
        pricing = self.selected_pricing

        processing_cost = ZERO
        interchange_passthrough = ZERO
        pricing_model_name = None

        if pricing:
            pricing_model_name = pricing.get_model_type_display()
            interac_count = to_decimal(a.interac_txn_count)
            interac_fee = to_decimal(pricing.per_transaction_fee) if pricing.per_transaction_fee else DEFAULT_INTERAC_FEE
            interac_cost = q(interac_count * interac_fee)
            monthly_fee = to_decimal(pricing.monthly_fee)

            if pricing.model_type == 'COST_PLUS':
                # Interchange pass-through + card brand fee + markup + Interac per-item
                interchange_passthrough = to_decimal(a.interchange_total)
                markup = to_decimal(pricing.markup_percent) if pricing.markup_percent else DEFAULT_COST_PLUS_MARKUP
                card_brand = to_decimal(pricing.card_brand_fee_percent) if pricing.card_brand_fee_percent else DEFAULT_COST_PLUS_CARD_BRAND
                markup_cost = q(monthly_volume * markup / Decimal('100'))
                card_brand_cost = q(monthly_volume * card_brand / Decimal('100'))
                processing_cost = interchange_passthrough + markup_cost + card_brand_cost + interac_cost + monthly_fee

            elif pricing.model_type == 'I_PLUS':
                # Interchange pass-through + bundled markup (NO separate card brand fee)
                interchange_passthrough = to_decimal(a.interchange_total)
                markup = to_decimal(pricing.markup_percent) if pricing.markup_percent else DEFAULT_IPLUS_MARKUP
                markup_cost = q(monthly_volume * markup / Decimal('100'))
                processing_cost = interchange_passthrough + markup_cost + interac_cost + monthly_fee

            elif pricing.model_type == 'DISCOUNT_RATE':
                # Per-brand base rates + billback on non-qualified volume + Interac per-item
                visa_vol = to_decimal(a.visa_volume)
                mc_vol = to_decimal(a.mc_volume)
                amex_vol = to_decimal(a.amex_volume)

                # Fallback: if brand splits not provided, use total volume with fallback rate
                if visa_vol == ZERO and mc_vol == ZERO and amex_vol == ZERO:
                    fallback_rate = to_decimal(pricing.discount_rate) if pricing.discount_rate else DEFAULT_VISA_RATE
                    visa_fee = q(monthly_volume * fallback_rate / Decimal('100'))
                    mc_fee = ZERO
                    amex_fee = ZERO
                else:
                    v_rate = to_decimal(pricing.visa_rate) if pricing.visa_rate else DEFAULT_VISA_RATE
                    m_rate = to_decimal(pricing.mc_rate) if pricing.mc_rate else DEFAULT_MC_RATE
                    a_rate = to_decimal(pricing.amex_rate) if pricing.amex_rate else DEFAULT_AMEX_RATE
                    visa_fee = q(visa_vol * v_rate / Decimal('100'))
                    mc_fee = q(mc_vol * m_rate / Decimal('100'))
                    amex_fee = q(amex_vol * a_rate / Decimal('100'))

                # Billback on non-qualified portion
                billback_cost = ZERO
                if pricing.nonqualified_pct and pricing.nonqualified_pct > ZERO:
                    nonqual_vol = q(monthly_volume * to_decimal(pricing.nonqualified_pct) / Decimal('100'))
                    b_rate = to_decimal(pricing.billback_rate) if pricing.billback_rate else DEFAULT_BILLBACK_RATE
                    billback_cost = q(nonqual_vol * b_rate / Decimal('100'))

                processing_cost = visa_fee + mc_fee + amex_fee + billback_cost + interac_cost + monthly_fee

            elif pricing.model_type == 'SURCHARGE':
                # Cardholder pays surcharge; merchant billed program discount on total ticket
                surcharge_rate = to_decimal(pricing.surcharge_rate) / Decimal('100')
                program_rate = to_decimal(pricing.program_discount_rate) / Decimal('100')
                surcharge_amount = q(monthly_volume * surcharge_rate)
                total_ticket = monthly_volume + surcharge_amount
                merchant_discount = q(total_ticket * program_rate)
                processing_cost = merchant_discount + monthly_fee

        # Proposed device costs
        device_monthly = ZERO
        device_onetime = ZERO
        for pd in self.proposed_devices:
            cost = to_decimal(pd.selected_price) * to_decimal(pd.quantity)
            if pd.pricing_type == 'LEASE':
                device_monthly += cost
            else:
                device_onetime += cost
        device_monthly = q(device_monthly)
        device_onetime = q(device_onetime)

        # Proposed SaaS costs
        saas_monthly = sum(
            (to_decimal(ps.monthly_cost) for ps in self.proposed_saas),
            ZERO
        )
        saas_monthly = q(saas_monthly)

        total_monthly = processing_cost + device_monthly + saas_monthly

        return {
            'pricing_model': pricing_model_name,
            'interchange_passthrough': float(q(interchange_passthrough)),
            'processing_cost': float(q(processing_cost)),
            'device_monthly': float(device_monthly),
            'device_onetime': float(device_onetime),
            'saas_monthly': float(saas_monthly),
            'total_monthly': float(q(total_monthly)),
        }

    # -------------------------------------------------------------------------
    # One-time Costs
    # -------------------------------------------------------------------------

    def calculate_onetime_costs(self):
        """Sum all one-time fees and device purchase costs."""
        required_fees = ZERO
        optional_fees = ZERO
        for fee in self.onetime_fees:
            if fee.is_optional:
                optional_fees += to_decimal(fee.amount)
            else:
                required_fees += to_decimal(fee.amount)

        proposed = self.calculate_proposed_costs()
        device_purchase = Decimal(str(proposed['device_onetime']))

        total = q(device_purchase + required_fees)

        return {
            'device_purchase': float(device_purchase),
            'required_fees': float(q(required_fees)),
            'optional_fees': float(q(optional_fees)),
            'total': float(total),
        }

    # -------------------------------------------------------------------------
    # Savings
    # -------------------------------------------------------------------------

    def calculate_savings(self, current_total, proposed_total, onetime_total):
        """Compute savings across timeframes and break-even."""
        current = Decimal(str(current_total))
        proposed = Decimal(str(proposed_total))
        onetime = Decimal(str(onetime_total))

        monthly = current - proposed

        savings_percent = ZERO
        if current > ZERO:
            savings_percent = q(monthly / current * Decimal('100'))

        daily = q(monthly / Decimal('30'))
        weekly = q(monthly * Decimal('12') / Decimal('52'))
        quarterly = q(monthly * Decimal('3'))
        yearly = q(monthly * Decimal('12'))

        break_even_months = None
        if monthly > ZERO and onetime > ZERO:
            break_even_months = float(q(onetime / monthly))
        elif onetime == ZERO:
            break_even_months = 0.0

        return {
            'monthly': float(q(monthly)),
            'percent': float(savings_percent),
            'daily': float(daily),
            'weekly': float(weekly),
            'quarterly': float(quarterly),
            'yearly': float(yearly),
            'break_even_months': break_even_months,
        }

    # -------------------------------------------------------------------------
    # Data Completeness Check
    # -------------------------------------------------------------------------

    def _check_data_completeness(self):
        """Return list of missing fields needed for a full calculation."""
        a = self.analysis
        missing = []

        if a.monthly_volume is None:
            missing.append('monthly_volume')
        if a.current_processing_rate is None:
            missing.append('current_processing_rate')
        if not self.selected_pricing:
            missing.append('pricing_model (none added)')
            return missing  # No point checking model-specific fields without a model

        model_type = self.selected_pricing.model_type

        if model_type in ('COST_PLUS', 'I_PLUS'):
            if a.interchange_total is None:
                missing.append('interchange_total (needed for Cost Plus / iPlus)')
        elif model_type == 'DISCOUNT_RATE':
            if a.visa_volume is None and a.mc_volume is None and a.amex_volume is None:
                missing.append('visa_volume / mc_volume / amex_volume (or total volume used as fallback)')
        elif model_type == 'SURCHARGE':
            if not self.selected_pricing.surcharge_rate:
                missing.append('surcharge_rate')
            if not self.selected_pricing.program_discount_rate:
                missing.append('program_discount_rate')

        return missing

    # -------------------------------------------------------------------------
    # Full Report
    # -------------------------------------------------------------------------

    def get_full_report(self):
        """
        Compute and return the complete cost comparison report.
        This is the main method called from the API view and admin panel.
        """
        missing_fields = self._check_data_completeness()
        has_sufficient_data = len(missing_fields) == 0

        current = self.calculate_current_costs()
        proposed = self.calculate_proposed_costs()
        onetime = self.calculate_onetime_costs()
        savings = self.calculate_savings(
            current['total_monthly'],
            proposed['total_monthly'],
            onetime['total'],
        )

        return {
            'analysis_id': self.analysis.id,
            'merchant': self.analysis.merchant.business_name,
            'has_sufficient_data': has_sufficient_data,
            'missing_fields': missing_fields,
            'current_costs': current,
            'proposed_costs': proposed,
            'onetime_costs': onetime,
            'savings': savings,
        }
