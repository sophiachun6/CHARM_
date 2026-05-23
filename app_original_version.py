from shiny import App, ui, render, reactive
import requests
from datetime import datetime

# =====================================================
# CHARM SCORE TABLE
# =====================================================

CHARM_TABLE = {

    0: 0.36,
    1: 1.89,
    2: 5.79,
    3: 12.97,
    4: 23.58,
    5: 34.15
}

# =====================================================
# OBSERVATION MAP
# =====================================================

OBSERVATION_MAP = {

    # =============================================
    # Vital Signs
    # =============================================

    "8310-5": {
        "label": "Temperature",
        "unit": "°C",
        "category": "Vital Signs"
    },

    "8867-4": {
        "label": "Heart Rate",
        "unit": "bpm",
        "category": "Vital Signs"
    },

    "9279-1": {
        "label": "Respiratory Rate",
        "unit": "/min",
        "category": "Vital Signs"
    },

    "59408-5": {
        "label": "SpO2",
        "unit": "%",
        "category": "Vital Signs"
    },

    # =============================================
    # Hematology
    # =============================================

    "789-8": {
        "label": "RBC",
        "unit": "",
        "category": "Hematology"
    },

    "6690-2": {
        "label": "WBC",
        "unit": "K/uL",
        "category": "Hematology"
    },

    "718-7": {
        "label": "Hemoglobin",
        "unit": "g/dL",
        "category": "Hematology"
    },

    "777-3": {
        "label": "Platelet",
        "unit": "K/uL",
        "category": "Hematology"
    },

    "788-0": {
        "label": "RDW",
        "unit": "%",
        "category": "Hematology"
    }
}

# =====================================================
# UI
# =====================================================

app_ui = ui.page_fluid(

    # =================================================
    # HASH PARAM
    # =================================================

    ui.tags.script("""
    (function () {

      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);

      function send() {

        if (window.Shiny && Shiny.setInputValue) {

          ["token","pid","fhir","obs"].forEach(k => {
            Shiny.setInputValue(k, params.get(k));
          });

        } else {

          setTimeout(send, 300);

        }
      }

      send();

    })();
    """),

    # =================================================
    # CSS
    # =================================================

    ui.tags.style("""

    body{
        background:#f4f7fb;
        font-family:Arial, Helvetica, sans-serif;
        padding:20px;
        color:#1e293b;
    }

    #token,#pid,#fhir,#obs{
        display:none !important;
    }

    .main-title{
        font-size:52px;
        font-weight:900;
        color:#0f172a;
        margin-bottom:6px;
    }

    .subtitle{
        font-size:18px;
        color:#64748b;
        margin-bottom:30px;
    }

    .custom-sidebar{
        background:white;
        border-radius:24px;
        padding:24px;
        box-shadow:0 10px 24px rgba(0,0,0,.08);
    }

    .card{
        background:white;
        border-radius:24px;
        padding:30px;
        margin-bottom:24px;
        box-shadow:0 10px 24px rgba(0,0,0,.08);
    }

    /* ============================================
       Patient Header
    ============================================ */

    .patient-header{
        background:linear-gradient(
            135deg,
            #2563eb,
            #1d4ed8
        );
        color:white;
        border-radius:24px;
        padding:34px;
        margin-bottom:24px;
        box-shadow:0 12px 28px rgba(0,0,0,.15);
    }

    .patient-name{
        font-size:40px;
        font-weight:900;
        margin-bottom:12px;
    }

    .patient-meta{
        font-size:17px;
        opacity:.92;
    }

    .last-update{
        margin-top:14px;
        font-size:14px;
        opacity:.85;
    }

    /* ============================================
       Risk
    ============================================ */

    .risk-center{
        text-align:center;
    }

    .risk-label{
        font-size:28px;
        font-weight:800;
        margin-bottom:8px;
    }

    .risk-number{
        font-size:110px;
        font-weight:900;
        line-height:1;
        margin-bottom:18px;
    }

    .risk-low{
        color:#16a34a;
    }

    .risk-mid{
        color:#f59e0b;
    }

    .risk-high{
        color:#dc2626;
    }

    .risk-bar{
        height:22px;
        border-radius:999px;
        background:linear-gradient(
            to right,
            #22c55e,
            #eab308,
            #ef4444
        );
        position:relative;
        overflow:hidden;
        margin-top:30px;
    }

    .risk-marker{
        position:absolute;
        top:-5px;
        width:6px;
        height:32px;
        background:black;
        border-radius:999px;
    }

    .clinical-note{
        margin-top:28px;
        background:#f8fafc;
        padding:20px;
        border-radius:18px;
        font-size:15px;
        line-height:1.7;
        color:#334155;
    }

    /* ============================================
       Findings
    ============================================ */

    .finding-item{
        border-radius:18px;
        padding:16px;
        margin-bottom:14px;
        display:flex;
        align-items:flex-start;
        gap:12px;
        font-weight:700;
        font-size:15px;
    }

    .finding-positive{
        background:#fef2f2;
        border:1px solid #fecaca;
        color:#b91c1c;
    }

    .finding-negative{
        background:#f8fafc;
        border:1px solid #e2e8f0;
        color:#64748b;
    }

    .finding-missing{
        background:#fff7ed;
        border:1px solid #fdba74;
        color:#c2410c;
    }

    .finding-icon{
        font-size:20px;
        margin-top:2px;
    }

    .finding-value{
        margin-top:5px;
        font-size:13px;
        opacity:.9;
        font-weight:500;
    }

    .badge{
        display:inline-block;
        margin-top:6px;
        padding:4px 10px;
        border-radius:999px;
        font-size:11px;
        font-weight:700;
    }

    .badge-auto{
        background:#dbeafe;
        color:#1d4ed8;
    }

    .badge-manual{
        background:#ede9fe;
        color:#6d28d9;
    }

    .badge-missing{
        background:#ffedd5;
        color:#c2410c;
    }

    /* ============================================
       Summary
    ============================================ */

    .summary-category{
        margin-top:30px;
        margin-bottom:12px;
        font-size:20px;
        font-weight:800;
        color:#0f172a;
    }

    .summary-table{
        width:100%;
        border-collapse:collapse;
    }

    .summary-table td{
        padding:18px;
        border-bottom:1px solid #e5e7eb;
        font-size:15px;
    }

    .summary-label{
        width:40%;
        color:#64748b;
        font-weight:700;
    }

    .summary-value{
        font-weight:800;
    }

    .summary-normal{
        color:#111827;
    }

    .summary-abnormal{
        color:#dc2626;
    }

    .summary-warning{
        color:#ea580c;
    }

    """),

    # =================================================
    # INPUTS
    # =================================================

    ui.input_text("token",""),
    ui.input_text("pid",""),
    ui.input_text("fhir",""),
    ui.input_text("obs",""),

    # Manual Override

    ui.input_radio_buttons(
        "manual_no_chills",
        None,
        {
            "auto":"Auto",
            "yes":"Yes",
            "no":"No"
        },
        selected="auto"
    ),

    ui.input_radio_buttons(
        "manual_malignancy",
        None,
        {
            "auto":"Auto",
            "yes":"Yes",
            "no":"No"
        },
        selected="auto"
    ),

    # =================================================
    # TITLE
    # =================================================

    ui.div(

        ui.div(
            "CHARM Sepsis Mortality Predictor",
            class_="main-title"
        ),

        ui.div(
            "AI-assisted in-hospital mortality risk estimation",
            class_="subtitle"
        )
    ),

    # =================================================
    # MAIN LAYOUT
    # =================================================

    ui.layout_sidebar(

        # =============================================
        # SIDEBAR
        # =============================================

        ui.sidebar(

            ui.div(

                {"class":"custom-sidebar"},

                ui.h4("Clinical Findings"),

                ui.hr(),

                ui.output_ui("clinical_findings")
            )
        ),

        # =============================================
        # MAIN CONTENT
        # =============================================

        ui.div(

            # =========================================
            # PATIENT HEADER
            # =========================================

            ui.div(

                {"class":"patient-header"},

                ui.output_ui("patient_header")
            ),

            # =========================================
            # RISK CARD
            # =========================================

            ui.div(

                {"class":"card risk-center"},

                ui.h3("Estimated In-hospital Mortality Risk"),

                ui.output_ui("risk_label"),

                ui.output_ui("prob"),

                ui.output_ui("risk_bar"),

                ui.output_ui("clinical_note"),

                ui.hr(),

                ui.h5("Top Contributing Factors"),

                ui.output_ui("top_factors"),

                ui.hr(),

                ui.h6("Reference"),

                ui.a(
                    "CHARM Score Research Paper",
                    href="https://pubmed.ncbi.nlm.nih.gov/27832977/",
                    target="_blank"
                ),

                ui.br(),
                ui.br(),

                ui.div("Produced by Dr. Chin-Chieh Wu"),

                ui.div("SMART on FHIR UI by Howard")
            ),

            # =========================================
            # SUMMARY
            # =========================================

            ui.div(

                {"class":"card"},

                ui.h4("Clinical Summary"),

                ui.output_ui("clinical_summary")
            )
        )
    )
)

# =====================================================
# SERVER
# =====================================================

def server(input, output, session):

    # =================================================
    # FETCH DATA
    # =================================================

    @reactive.Calc
    def fhir_data():

        if not (
            input.token()
            and input.pid()
            and input.fhir()
        ):
            return {}

        headers = {

            "Authorization":
            f"Bearer {input.token()}",

            "Accept":
            "application/fhir+json"
        }

        data = {}

        try:

            patient_response = requests.get(

                f"{input.fhir()}/Patient/{input.pid()}",

                headers=headers,

                timeout=10,

                verify=False
            )

            data["patient"] = patient_response.json()

            if input.obs():

                obs_response = requests.get(

                    input.obs(),

                    headers=headers,

                    timeout=10,

                    verify=False
                )

                data["observation"] = obs_response.json()

        except Exception as e:

            data["error"] = str(e)

        return data

    # =================================================
    # FACTOR STATE
    # =================================================

    @reactive.Calc
    def factor_state():

        obs = fhir_data().get("observation", {})

        result = {

            "no_chills": None,
            "hypothermia": None,
            "anemia": None,
            "rdw": None,
            "malignancy": None
        }

        if "component" not in obs:
            return result

        for c in obs["component"]:

            code = c.get(
                "code",{}
            ).get(
                "coding",[{}]
            )[0].get("code")

            value = c.get(
                "valueQuantity",{}
            ).get("value")

            # Temperature

            if code == "8310-5":

                if value is not None:

                    result["hypothermia"] = value < 36

            # RBC

            elif code == "789-8":

                if value is not None:

                    result["anemia"] = value < 4

            # RDW

            elif code == "788-0":

                if value is not None:

                    result["rdw"] = value > 14.5

        # =============================================
        # MANUAL OVERRIDE
        # =============================================

        if input.manual_no_chills() == "yes":
            result["no_chills"] = True

        elif input.manual_no_chills() == "no":
            result["no_chills"] = False

        if input.manual_malignancy() == "yes":
            result["malignancy"] = True

        elif input.manual_malignancy() == "no":
            result["malignancy"] = False

        return result

    # =================================================
    # SCORE
    # =================================================

    def score():

        f = factor_state()

        total = 0

        for v in f.values():

            if v is True:
                total += 1

        return total

    # =================================================
    # PATIENT HEADER
    # =================================================

    @output
    @render.ui
    def patient_header():

        data = fhir_data()

        patient = data.get("patient", {})

        obs = data.get("observation", {})

        try:

            family = patient["name"][0]["family"]

            given = patient["name"][0]["given"][0]

            fullname = f"{given} {family}"

        except:

            fullname = "Unknown Patient"

        gender = patient.get("gender", "Unknown")

        updated = obs.get(
            "lastUpdated",
            "Unknown"
        )

        return ui.div(

            ui.div(
                fullname,
                class_="patient-name"
            ),

            ui.div(
                f"Patient ID: {input.pid()} • Gender: {gender}",
                class_="patient-meta"
            ),

            ui.div(
                f"Last Updated: {updated}",
                class_="last-update"
            )
        )

    # =================================================
    # RISK LABEL
    # =================================================

    @output
    @render.ui
    def risk_label():

        p = CHARM_TABLE.get(score(),0)

        if p < 5:

            return ui.div(
                "VERY LOW RISK",
                class_="risk-label risk-low"
            )

        elif p < 20:

            return ui.div(
                "MODERATE RISK",
                class_="risk-label risk-mid"
            )

        else:

            return ui.div(
                "HIGH RISK",
                class_="risk-label risk-high"
            )

    # =================================================
    # PROB
    # =================================================

    @output
    @render.ui
    def prob():

        p = CHARM_TABLE.get(score(),0)

        cls = (
            "risk-low"
            if p < 5 else
            "risk-mid"
            if p < 20 else
            "risk-high"
        )

        return ui.div(

            f"{p:.2f}%",

            class_=f"risk-number {cls}"
        )

    # =================================================
    # RISK BAR
    # =================================================

    @output
    @render.ui
    def risk_bar():

        p = CHARM_TABLE.get(score(),0)

        left = min(p / 40 * 100, 100)

        return ui.div(

            {"class":"risk-bar"},

            ui.div({

                "class":"risk-marker",

                "style":f"left:{left}%"
            })
        )

    # =================================================
    # CLINICAL NOTE
    # =================================================

    @output
    @render.ui
    def clinical_note():

        p = CHARM_TABLE.get(score(),0)

        if p < 5:

            note = (
                "Patient currently demonstrates low mortality risk. "
                "Continue routine monitoring and standard care."
            )

        elif p < 20:

            note = (
                "Moderate mortality risk detected. "
                "Recommend closer observation and repeat laboratory evaluation."
            )

        else:

            note = (
                "High mortality risk detected. "
                "Consider ICU evaluation and urgent clinical escalation."
            )

        return ui.div(

            note,

            class_="clinical-note"
        )

    # =================================================
    # TOP FACTORS
    # =================================================

    @output
    @render.ui
    def top_factors():

        f = factor_state()

        factors = []

        if f["hypothermia"]:
            factors.append("• Hypothermia detected")

        if f["anemia"]:
            factors.append("• Anemia detected")

        if f["rdw"]:
            factors.append("• Elevated RDW detected")

        if f["malignancy"]:
            factors.append("• Malignancy history")

        if f["no_chills"]:
            factors.append("• No chills reported")

        if len(factors) == 0:
            factors.append("• No major contributing factors")

        return ui.tags.ul(

            *[
                ui.tags.li(x)
                for x in factors
            ]
        )

    # =================================================
    # FINDINGS
    # =================================================

    @output
    @render.ui
    def clinical_findings():

        f = factor_state()

        findings = [

            (
                "No Chills",
                f["no_chills"],
                "Manual / Missing Data"
            ),

            (
                "Hypothermia",
                f["hypothermia"],
                "Temperature < 36°C"
            ),

            (
                "Anemia",
                f["anemia"],
                "RBC < 4"
            ),

            (
                "RDW Elevation",
                f["rdw"],
                "RDW > 14.5%"
            ),

            (
                "Malignancy History",
                f["malignancy"],
                "Manual / Missing Data"
            )
        ]

        cards = []

        for label, value, detail in findings:

            # =========================================
            # STATUS
            # =========================================

            if value is True:

                icon = "✓"

                cls = (
                    "finding-item finding-positive"
                )

                badge = ui.div(
                    "AUTO DETECTED",
                    class_="badge badge-auto"
                )

            elif value is False:

                icon = "✗"

                cls = (
                    "finding-item finding-negative"
                )

                badge = ui.div(
                    "NORMAL",
                    class_="badge badge-auto"
                )

            else:

                icon = "?"

                cls = (
                    "finding-item finding-missing"
                )

                badge = ui.div(
                    "NO DATA",
                    class_="badge badge-missing"
                )

            cards.append(

                ui.div(

                    {"class":cls},

                    ui.div(
                        icon,
                        class_="finding-icon"
                    ),

                    ui.div(

                        ui.div(label),

                        ui.div(
                            detail,
                            class_="finding-value"
                        ),

                        badge
                    )
                )
            )

        return ui.div(*cards)

    # =================================================
    # SUMMARY
    # =================================================

    @output
    @render.ui
    def clinical_summary():

        obs = fhir_data().get("observation", {})

        if "component" not in obs:

            return ui.div("No clinical data")

        grouped = {}

        for c in obs["component"]:

            code = c.get(
                "code",{}
            ).get(
                "coding",[{}]
            )[0].get("code")

            if code not in OBSERVATION_MAP:
                continue

            config = OBSERVATION_MAP[code]

            category = config["category"]

            label = config["label"]

            unit = config["unit"]

            value = c.get(
                "valueQuantity",{}
            ).get("value")

            if value is None:
                continue

            display = f"{value} {unit}"

            css = "summary-value summary-normal"

            # =========================================
            # Abnormal Highlight
            # =========================================

            if (
                code == "8310-5"
                and value < 36
            ):
                css = (
                    "summary-value summary-abnormal"
                )

            elif (
                code == "789-8"
                and value < 4
            ):
                css = (
                    "summary-value summary-abnormal"
                )

            elif (
                code == "788-0"
                and value > 14.5
            ):
                css = (
                    "summary-value summary-warning"
                )

            row = ui.tags.tr(

                ui.tags.td(
                    label,
                    class_="summary-label"
                ),

                ui.tags.td(
                    display,
                    class_=css
                )
            )

            if category not in grouped:
                grouped[category] = []

            grouped[category].append(row)

        sections = []

        for category, rows in grouped.items():

            sections.append(

                ui.div(

                    ui.div(
                        category,
                        class_="summary-category"
                    ),

                    ui.tags.table(

                        {"class":"summary-table"},

                        *rows
                    )
                )
            )

        return ui.div(*sections)

# =====================================================
# APP
# =====================================================

app = App(app_ui, server)
