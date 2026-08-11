"""Structured stock and sector research summaries."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from stock_analysis.data import PEER_GROUPS, clean_ticker


SECTOR_PROFILES = {
    "mega_cap_tech": {
        "demand": [
            "Demand is driven by cloud adoption, AI infrastructure, enterprise software spending, device replacement cycles, and digital advertising budgets.",
            "Long-term growth depends on continued digital adoption, productivity software penetration, and consumer ecosystem expansion.",
        ],
        "competition": [
            "The industry is concentrated among a few scale platforms with strong distribution, brand recognition, data advantages, and deep capital resources.",
            "Incumbents often have pricing power, but competition is intense in AI, cloud, devices, advertising, and developer platforms.",
        ],
        "regulation": [
            "Antitrust scrutiny, privacy rules, app-store policy, AI governance, and global tax policy can affect margins and strategic flexibility.",
            "Trade restrictions on chips, cloud infrastructure, and China exposure can alter supply chains and customer access.",
        ],
        "competitors": [
            "Major players include Apple, Microsoft, Alphabet, Meta, Nvidia, and Amazon.",
            "Strategies center on AI integration, cloud scale, subscription growth, platform lock-in, and proprietary hardware or infrastructure.",
        ],
        "risks": [
            "Key risks include valuation compression from higher rates, AI capital-spending overruns, regulatory penalties, product-cycle weakness, and platform disruption.",
            "Supply-chain concentration and geopolitical limits on China-related demand can create earnings volatility.",
        ],
    },
    "semiconductors": {
        "demand": [
            "Demand is driven by AI accelerators, cloud data centers, autos, industrial automation, PCs, smartphones, and memory cycles.",
            "Energy-efficient computing, advanced packaging, and edge AI are important long-term growth drivers.",
        ],
        "competition": [
            "The sector is concentrated in leading-edge design and foundry capacity, with high barriers from IP, fabrication complexity, and customer qualification.",
            "Pricing power varies by product cycle; AI and specialized accelerators currently have stronger pricing than commodity memory.",
        ],
        "regulation": [
            "Export controls, chip subsidies, national-security policy, and Taiwan supply-chain concentration are central policy variables.",
            "Trade restrictions can shift demand, capacity planning, and customer access.",
        ],
        "competitors": [
            "Major players include Nvidia, AMD, Broadcom, Intel, TSMC, Qualcomm, and Micron.",
            "Strategies focus on AI platforms, packaging, software ecosystems, and long-term supply agreements.",
        ],
        "risks": [
            "Key risks include cyclical inventory corrections, technology-node delays, export restrictions, supply shortages, and rapid product substitution.",
            "Heavy capital spending and concentrated customer demand can amplify earnings volatility.",
        ],
    },
    "ev_auto": {
        "demand": [
            "Demand is driven by vehicle replacement cycles, EV adoption, battery costs, charging infrastructure, fleet demand, and consumer credit conditions.",
            "Urbanization, emissions targets, and autonomous-driving investment remain long-term growth drivers.",
        ],
        "competition": [
            "The industry is competitive and capital intensive, with scale, manufacturing efficiency, brand, and dealer or direct-sales reach shaping returns.",
            "Pricing power is limited when inventory rises or financing costs pressure affordability.",
        ],
        "regulation": [
            "Emissions standards, EV credits, tariffs, safety rules, and autonomous-driving regulation materially affect demand and margins.",
            "Battery sourcing rules and trade policy can change production economics.",
        ],
        "competitors": [
            "Major players include Tesla, Toyota, GM, Ford, Rivian, and BYD globally.",
            "Strategies vary from software-defined vehicles to hybrid platforms and high-volume cost leadership.",
        ],
        "risks": [
            "Key risks include cyclical downturns, price wars, battery raw-material volatility, recalls, execution delays, and policy changes.",
            "Higher interest rates can weaken affordability and pressure unit demand.",
        ],
    },
    "banks": {
        "demand": [
            "Demand is driven by loan growth, capital-markets activity, consumer credit, business formation, and yield-curve conditions.",
            "Deposit stability and fee income help determine resilience through economic cycles.",
        ],
        "competition": [
            "The sector is concentrated among large banks but fragmented across regional lenders, fintechs, private credit, and asset managers.",
            "Scale, deposit franchises, risk controls, and regulatory capacity are major barriers to entry.",
        ],
        "regulation": [
            "Capital rules, stress tests, liquidity standards, consumer-protection rules, and bank-merger policy directly shape returns.",
            "Fiscal policy and central-bank rates influence credit demand, defaults, and net interest margins.",
        ],
        "competitors": [
            "Major players include JPMorgan, Bank of America, Wells Fargo, Citi, Goldman Sachs, and Morgan Stanley.",
            "Strategies center on deposit scale, wealth management, trading, investment banking, and disciplined credit underwriting.",
        ],
        "risks": [
            "Key risks include credit losses, deposit flight, yield-curve compression, regulatory capital increases, and market-liquidity shocks.",
            "Commercial real estate and consumer delinquencies can weigh on sector sentiment.",
        ],
    },
    "healthcare": {
        "demand": [
            "Demand is driven by aging populations, chronic disease prevalence, drug innovation, insurance coverage, and procedure volumes.",
            "Biologics, obesity care, oncology, and medical technology are major growth areas.",
        ],
        "competition": [
            "The industry has strong barriers from patents, clinical data, regulatory approvals, provider networks, and scale purchasing.",
            "Pricing power varies by product exclusivity, reimbursement, and generic or biosimilar risk.",
        ],
        "regulation": [
            "Drug pricing, reimbursement, FDA approvals, Medicare policy, and global health budgets can materially alter growth and margins.",
            "Patent cliffs and exclusivity periods are central policy and legal considerations.",
        ],
        "competitors": [
            "Major players include Eli Lilly, UnitedHealth, Johnson & Johnson, Merck, Pfizer, and AbbVie.",
            "Strategies focus on pipeline productivity, managed-care scale, acquisitions, and specialty-drug franchises.",
        ],
        "risks": [
            "Key risks include clinical failures, pricing pressure, patent expirations, reimbursement changes, and litigation.",
            "Regulatory setbacks can quickly change earnings expectations.",
        ],
    },
    "consumer": {
        "demand": [
            "Demand is driven by employment, wage growth, consumer confidence, housing activity, e-commerce adoption, and household balance sheets.",
            "Digital channels, membership models, and value-seeking behavior are important demand drivers.",
        ],
        "competition": [
            "The sector ranges from concentrated scale retailers to fragmented apparel and specialty categories.",
            "Pricing power depends on brand strength, inventory discipline, supplier scale, and customer loyalty.",
        ],
        "regulation": [
            "Tariffs, labor rules, consumer-credit regulation, product safety, and data privacy can affect costs and demand.",
            "Fiscal stimulus or tax changes can influence discretionary spending.",
        ],
        "competitors": [
            "Major players include Amazon, Walmart, Costco, Target, Home Depot, Lowe's, and Nike.",
            "Strategies emphasize logistics, private label, membership, omnichannel reach, and brand differentiation.",
        ],
        "risks": [
            "Key risks include consumer slowdowns, inventory markdowns, freight costs, wage inflation, and channel disruption.",
            "Exchange rates can pressure multinational revenue and sourcing costs.",
        ],
    },
    "energy": {
        "demand": [
            "Demand is driven by global industrial activity, transportation, petrochemicals, power demand, and energy-transition investment.",
            "LNG, grid investment, and disciplined upstream spending are important structural drivers.",
        ],
        "competition": [
            "The industry is global and commodity-linked, with cost-curve position, reserve quality, and integrated operations shaping resilience.",
            "Pricing power is limited by commodity markets, though low-cost producers can earn stronger through-cycle returns.",
        ],
        "regulation": [
            "Environmental rules, drilling permits, carbon policy, sanctions, OPEC policy, and tax regimes can significantly affect supply and profitability.",
            "Energy-security policy can support investment even as decarbonization pressure rises.",
        ],
        "competitors": [
            "Major players include Exxon Mobil, Chevron, ConocoPhillips, SLB, EOG, and Marathon Petroleum.",
            "Strategies focus on low-cost reserves, capital discipline, shareholder returns, LNG, and selective transition investments.",
        ],
        "risks": [
            "Key risks include commodity price swings, geopolitical supply shocks, regulatory constraints, reserve depletion, and execution risk.",
            "Energy transition and demand substitution can pressure long-duration assets.",
        ],
    },
    "indexes": {
        "demand": [
            "Demand is influenced by broad equity flows, earnings growth, retirement contributions, passive investing, and risk appetite.",
            "GDP growth, inflation, interest rates, and fiscal policy are the primary macro drivers.",
        ],
        "competition": [
            "Broad market funds are highly concentrated among large ETF sponsors and compete mainly on cost, liquidity, tracking quality, and brand.",
            "Underlying sector concentration can drive performance even when the product is diversified.",
        ],
        "regulation": [
            "Market-structure rules, tax policy, retirement policy, and disclosure standards can influence flows and investor behavior.",
            "Central-bank policy has a major impact on equity valuation multiples.",
        ],
        "competitors": [
            "Major products include SPY, VOO, IVV, QQQ, DIA, and IWM.",
            "Competitive advantages come from liquidity, low fees, index brand, and distribution reach.",
        ],
        "risks": [
            "Key risks include valuation compression, earnings recession, geopolitical shocks, liquidity events, and sector concentration.",
            "Inflation or rate surprises can change factor leadership quickly.",
        ],
    },
}

MOAT_PROFILES = {
    "mega_cap_tech": [
        "Intangible assets: brand, patents, software ecosystems, proprietary data, and developer relationships can support durable demand.",
        "Switching costs: embedded workflows, app ecosystems, cloud migrations, and identity systems can make customers less likely to leave.",
        "Network effects: platforms become stronger when users, advertisers, developers, and enterprise customers reinforce one another.",
        "Cost advantage: scale in infrastructure, procurement, distribution, and R&D can lower unit costs versus smaller rivals.",
    ],
    "semiconductors": [
        "Intangible assets: chip architecture, patents, software stacks, and design expertise can create differentiation.",
        "Switching costs: customer qualification cycles and software compatibility can make platform changes slow and expensive.",
        "Cost advantage: scale purchasing, foundry access, packaging expertise, and yield learning can protect margins.",
        "Network effects: developer tools and ecosystem support can reinforce adoption for leading platforms.",
    ],
    "ev_auto": [
        "Intangible assets: brand, software, battery know-how, and safety reputation can help sustain demand.",
        "Switching costs: charging networks, service access, fleet tools, and software features can improve retention.",
        "Cost advantage: manufacturing scale, battery sourcing, and platform reuse can support pricing flexibility.",
        "Network effects: charging infrastructure and connected-vehicle data can improve the owner experience over time.",
    ],
    "banks": [
        "Intangible assets: trusted brands, regulatory licenses, client relationships, and risk-management culture are meaningful advantages.",
        "Switching costs: deposits, treasury services, lending relationships, and wealth-management accounts can be sticky.",
        "Cost advantage: low-cost deposits and scale technology spending can support returns through cycles.",
        "Network effects: payment networks and institutional client ecosystems can strengthen large financial platforms.",
    ],
    "healthcare": [
        "Intangible assets: patents, clinical data, regulatory approvals, and physician trust can protect economics.",
        "Switching costs: formulary placement, provider workflows, and patient continuity can support retention.",
        "Cost advantage: manufacturing scale, purchasing power, and global commercial reach can improve margins.",
        "Network effects: healthcare networks and clinical evidence can reinforce adoption for leading therapies or platforms.",
    ],
    "consumer": [
        "Intangible assets: brand equity, private label, loyalty programs, and merchandising expertise can support repeat demand.",
        "Switching costs: memberships, subscriptions, rewards, and habit formation can improve retention.",
        "Cost advantage: logistics scale, supplier leverage, and store or fulfillment density can protect margins.",
        "Network effects: marketplaces and membership ecosystems can become more valuable as assortment and customers grow.",
    ],
    "energy": [
        "Intangible assets: technical expertise, reserves knowledge, project execution, and safety reputation are key advantages.",
        "Switching costs: long-term customer contracts, infrastructure integration, and service relationships can support retention.",
        "Cost advantage: advantaged acreage, integrated assets, and disciplined operations can improve through-cycle returns.",
        "Network effects: midstream and trading networks can improve reliability and market access.",
    ],
    "indexes": [
        "Intangible assets: index brand, product trust, and sponsor reputation support investor adoption.",
        "Switching costs: tax considerations, retirement-plan defaults, and embedded portfolio workflows can make holdings sticky.",
        "Cost advantage: scale allows large ETF sponsors to offer low fees and high liquidity.",
        "Network effects: liquidity improves as more investors, market makers, and institutions use the same vehicle.",
    ],
}


def _group_key_for_symbol(symbol: str) -> str:
    for key, group in PEER_GROUPS.items():
        if symbol in group["symbols"]:
            return key
    return "indexes"


def _is_number(value: object) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return pd.notna(number)


def _format_percent(value: object) -> str:
    if not _is_number(value):
        return "not available"
    number = float(value)
    if abs(number) > 2:
        number = number / 100
    return f"{number:.1%}"


def _format_currency(value: object) -> str:
    if not _is_number(value):
        return "not available"
    number = float(value)
    for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(number) >= threshold:
            return f"${number / threshold:.2f}{suffix}"
    return f"${number:,.0f}"


def _format_ratio(value: object) -> str:
    if not _is_number(value):
        return "not available"
    return f"{float(value):.2f}x"


def _first_row(frame: pd.DataFrame, names: list[str]) -> pd.Series | None:
    if frame is None or frame.empty:
        return None
    for name in names:
        if name in frame.index:
            return frame.loc[name]
    lower_lookup = {str(index).lower(): index for index in frame.index}
    for name in names:
        key = lower_lookup.get(name.lower())
        if key is not None:
            return frame.loc[key]
    return None


def _clean_statement(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    data = data.loc[:, ~data.columns.duplicated()]
    return data.sort_index(axis=1, ascending=False)


def _margin_summary(ticker_obj: yf.Ticker) -> list[str]:
    try:
        income = _clean_statement(ticker_obj.income_stmt)
    except Exception:
        income = pd.DataFrame()
    revenue = _first_row(income, ["Total Revenue", "Operating Revenue"])
    gross_profit = _first_row(income, ["Gross Profit"])
    operating_income = _first_row(income, ["Operating Income", "Operating Income Loss"])
    net_income = _first_row(income, ["Net Income", "Net Income Common Stockholders"])

    if revenue is None:
        return ["Margin history: annual revenue detail was not available from Yahoo Finance for a 5-10 year view."]

    def summarize(label: str, row: pd.Series | None) -> str:
        if row is None:
            return f"{label}: not available."
        margins = (row / revenue).dropna()
        margins = margins[(margins != float("inf")) & (margins != float("-inf"))]
        if margins.empty:
            return f"{label}: not available."
        margins = margins.head(10)
        latest = margins.iloc[0]
        low = margins.min()
        high = margins.max()
        years = len(margins)
        return (
            f"{label}: latest {latest:.1%}; available annual range {low:.1%} to {high:.1%} "
            f"across {years} reported year{'s' if years != 1 else ''}."
        )

    return [
        summarize("Gross margin", gross_profit),
        summarize("Operating margin", operating_income),
        summarize("Net margin", net_income),
    ]


def _latest_cashflow_value(frame: pd.DataFrame, names: list[str]) -> float | None:
    row = _first_row(frame, names)
    if row is None:
        return None
    values = row.dropna()
    if values.empty:
        return None
    return float(values.iloc[0])


def _free_cash_flow(ticker_obj: yf.Ticker, info: dict) -> str:
    if _is_number(info.get("freeCashflow")):
        return _format_currency(info.get("freeCashflow"))

    try:
        cashflow = _clean_statement(ticker_obj.cashflow)
    except Exception:
        cashflow = pd.DataFrame()
    free_cash_flow = _latest_cashflow_value(cashflow, ["Free Cash Flow"])
    if free_cash_flow is not None:
        return _format_currency(free_cash_flow)

    operating_cash_flow = _latest_cashflow_value(
        cashflow,
        ["Operating Cash Flow", "Total Cash From Operating Activities"],
    )
    capex = _latest_cashflow_value(cashflow, ["Capital Expenditure", "Capital Expenditures"])
    if operating_cash_flow is None or capex is None:
        return "not available"
    return _format_currency(operating_cash_flow + capex)


def _buyback_summary(ticker_obj: yf.Ticker) -> str:
    try:
        cashflow = _clean_statement(ticker_obj.cashflow)
    except Exception:
        cashflow = pd.DataFrame()
    repurchases = _first_row(
        cashflow,
        ["Repurchase Of Capital Stock", "Repurchase Of Stock", "Common Stock Repurchased"],
    )
    if repurchases is None:
        return "Share buybacks: repurchase history was not available from Yahoo Finance."
    values = repurchases.dropna().head(5)
    if values.empty:
        return "Share buybacks: repurchase history was not available from Yahoo Finance."
    total = values.sum()
    if total < 0:
        return f"Share buybacks: approximately {_format_currency(abs(total))} returned through repurchases across the latest reported years."
    return "Share buybacks: no clear recent repurchase outflow was visible in the latest reported cash-flow statements."


def _debt_assessment(debt_to_equity: object) -> str:
    if not _is_number(debt_to_equity):
        return "Debt to equity: not available; review the latest balance sheet before judging leverage."
    raw_ratio = float(debt_to_equity)
    ratio = raw_ratio / 100 if raw_ratio > 10 else raw_ratio
    if ratio < 0.5:
        view = "low leverage"
    elif ratio < 1.5:
        view = "moderate leverage"
    else:
        view = "elevated leverage"
    return f"Debt to equity: {_format_ratio(ratio)}, suggesting {view}."


def _liquidity_assessment(current_ratio: object) -> str:
    if not _is_number(current_ratio):
        return "Current ratio: not available; liquidity needs a direct balance-sheet review."
    ratio = float(current_ratio)
    if ratio >= 2:
        view = "strong short-term liquidity"
    elif ratio >= 1:
        view = "adequate short-term liquidity"
    else:
        view = "tight short-term liquidity"
    return f"Current ratio: {_format_ratio(ratio)}, suggesting {view}."


def build_company_research(ticker: str, info: dict) -> dict[str, list[str]]:
    """Build concise company research bullets from live fields and sector context."""
    symbol = clean_ticker(ticker)
    ticker_obj = yf.Ticker(symbol)
    group_key = _group_key_for_symbol(symbol)
    officers = info.get("companyOfficers") or []
    leadership = [
        f"{officer.get('name')} - {officer.get('title')}"
        for officer in officers
        if officer.get("name") and officer.get("title")
    ][:3]
    insider_ownership = info.get("heldPercentInsiders")

    return {
        "profitability": [
            f"Return on equity (ROE): {_format_percent(info.get('returnOnEquity'))}.",
            f"Return on assets (ROA): {_format_percent(info.get('returnOnAssets'))}.",
            *_margin_summary(ticker_obj),
            f"Free cash flow (FCF): {_free_cash_flow(ticker_obj, info)}.",
            _debt_assessment(info.get("debtToEquity")),
            _liquidity_assessment(info.get("currentRatio")),
        ],
        "moat": MOAT_PROFILES.get(group_key, MOAT_PROFILES["indexes"]),
        "management": [
            (
                "Leadership team: "
                + ("; ".join(leadership) if leadership else "leadership detail was not available from Yahoo Finance.")
                + "."
            ),
            _buyback_summary(ticker_obj),
            "Growth investment: review R&D, capital expenditures, and acquisitions to judge whether reinvestment is expanding the moat.",
            (
                f"Alignment of interests: insiders hold {_format_percent(insider_ownership)} of shares outstanding."
                if _is_number(insider_ownership)
                else "Alignment of interests: insider ownership was not available from Yahoo Finance."
            ),
        ],
    }


def build_sector_research(news_context: dict) -> dict[str, list[str]]:
    """Build concise sector research bullets."""
    symbol = news_context.get("symbol", "")
    group_key = _group_key_for_symbol(symbol)
    profile = SECTOR_PROFILES.get(group_key, SECTOR_PROFILES["indexes"])
    market_label = news_context.get("market_label", "the sector")
    articles = news_context.get("market_articles") or []
    headlines = [article["title"].rstrip(".") for article in articles[:3] if article.get("title")]
    recent_headlines = (
        [f"Recent headline: {headline}." for headline in headlines]
        if headlines
        else [f"Recent headlines: no current Yahoo Finance headlines were available for {market_label}."]
    )

    return {
        "Macro and economic environment": [
            "Interest rates: higher rates can pressure valuation multiples and financing-sensitive demand; lower rates can support risk appetite.",
            "Inflation: margin impact depends on pricing power, wage pressure, input costs, and contract flexibility.",
            "GDP growth and fiscal policy: stronger growth and supportive fiscal spending usually help revenue momentum; slowdowns raise earnings risk.",
            "Exchange rates: a stronger U.S. dollar can reduce translated overseas revenue for global firms.",
        ],
        "Industry demand and growth drivers": profile["demand"],
        "Competitive landscape": profile["competition"],
        "Regulatory and policy factors": profile["regulation"],
        "Industry performance metrics": [
            "Track sector revenue growth, operating margins, earnings revisions, and cash-flow conversion to judge health.",
            "Watch market share shifts among incumbents and challengers for evidence of durable pricing power or disruption.",
        ],
        "SWOT analysis": [
            f"Strengths: scale leaders in {market_label} often benefit from brand, distribution, capital access, and customer relationships.",
            "Weaknesses: high expectations, cyclicality, regulation, and execution complexity can compress returns.",
            "Opportunities: innovation, international expansion, productivity gains, and adjacent-market entry can extend growth.",
            "Threats: disruption, policy changes, macro shocks, and aggressive price competition can weaken margins.",
        ],
        "Key competitors and market players": profile["competitors"],
        "Risk assessment": profile["risks"],
        "Sentiment and market research": [
            "Analyst coverage: monitor estimate revisions, target-price changes, and downgrade or upgrade clusters.",
            "Market sentiment: compare sector ETF performance, fund flows, valuation spreads, and earnings-revision breadth.",
            *recent_headlines,
        ],
    }
