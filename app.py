from shiny import App, ui, render, reactive
import requests

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

    # Temperature
    "8310-5": {
        "label": "Temperature",
        "unit": "°C"
    },

    # RBC
    "789-8": {
        "label": "RBC",
        "unit": ""
    },

    # RDW
    "788-0": {
        "label": "RDW",
        "unit": "%"
    },

    # WBC
    "6690-2": {
        "label": "WBC",
        "unit": "K/uL"
    },

    # Hemoglobin
    "718-7": {
        "label": "Hemoglobin",
        "unit": "g/dL"
    },

    # Platelet
    "777-3": {
        "label": "Platelet",
        "unit": "K/uL"
    },

    # Heart Rate
    "8867-4": {
        "label": "Heart Rate",
        "unit": "bpm"
    },

    # Respiratory Rate
    "9279-1": {
        "label": "Respiratory Rate",
        "unit": "/min"
    },

    # SpO2
    "59408-5": {
        "label": "SpO2",
        "unit": "%"
    }
}

# =====================================================
# UI
# =====================================================

app_ui = ui.page_fluid(

    # =================================================
    # URL HASH → SHINY INPUT
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
        background:#f3f6fb;
        font-family:Arial, Helvetica, sans-serif;
        padding:20px;
        color:#1f2937;
    }

    #token,#pid,#fhir,#obs{
        display:none !important;
    }

    .main-title{
        font-size:48px;
        font-weight:900;
        margin-bottom:6px;
        color:#0f172a;
    }

    .subtitle{
        color:#64748b;
        margin-bottom:28px;
        font-size:18px;
    }

    .custom-sidebar{
        background:white;
        border-radius:24px;
        padding:24px;
        box-shadow:0 8px 24px rgba(0,0,0,.08);
    }

    .card{
        background:white;
        border-radius:24px;
        padding:30px;
        margin-bottom:24px;
        box-shadow:0 8px 24px rgba(0,0,0,.08);
    }

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
        font-size:38px;
        font-weight:900;
        margin-bottom:10px;
    }

    .patient-meta{
        font-size:16px;
        opacity:.92;
    }

    .last-update{
        margin-top:12px;
        font-size:14px;
        opacity:.82;
    }

    .risk-center{
        text-align:center;
    }

    .risk-number{
        font-size:100px;
        font-weight:900;
        line-height:1;
        margin-top:10px;
        margin-bottom:14px;
    }

    .risk-label{
        font-size:28px;
        font-weight:800;
        margin-bottom:10px;
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
        height:20px;
        border-radius:999px;
        background:linear-gradient(
            to right,
            #22c55e,
            #eab308,
            #ef4444
        );
        margin-top:30px;
        position:relative;
        overflow:hidden;
    }

    .risk-marker{
        position:absolute;
        top:-5px;
        width:6px;
        height:30px;
        background:black;
        border-radius:999px;
    }

    .clinical-note{
        margin-top:26px;
        padding:20px;
        border-radius:18px;
        background:#f8fafc;
        color:#334155;
        font-size:15px;
        line-height:1.7;
    }

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
        color:#b91c1c;
        border:1px solid #fecaca;
    }

    .finding-negative{
        background:#f8fafc;
        color:#64748b;
        border:1px solid #e2e8f0;
    }

    .finding-icon{
        font-size:20px;
        margin-top:2px;
    }

    .finding-value{
        margin-top:4px;
        font-size:13px;
        font-weight:500;
        opacity:.9;
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
    # HIDDEN INPUTS
    # =================================================

    ui.input_text("token",""),
    ui.input_text("pid",""),
    ui.input_text("fhir",""),
    ui.input_text("obs",""),

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
            # CLINICAL SUMMARY
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
    # FETCH FHIR DATA
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

                verify=False,

                timeout=10
            )

            data["patient"] = patient_response.json()

            if input.obs():

                obs_response = requests.get(

                    input.obs(),

                    headers=headers,

                    verify=False,

                    timeout=10
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

        factors = {

            "no_chills": False,
            "hypothermia": False,
            "anemia": False,
            "rdw": False,
            "malignancy": False
        }

        if "component" not in obs:
            return factors

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

            if (
                code == "8310-5"
                and value is not None
                and value < 36
            ):
                factors["hypothermia"] = True

            # RBC

            elif (
                code == "789-8"
                and value is not None
                and value < 4
            ):
                factors["anemia"] = True

            # RDW

            elif (
                code == "788-0"
                and value is not None
                and value > 14.5
            ):
                factors["rdw"] = True

        return factors

    # =================================================
    # SCORE
    # =================================================

    def score():

        f = factor_state()

        return sum([

            f["no_chills"],

            f["hypothermia"],

            f["anemia"],

            f["rdw"],

            f["malignancy"]
        ])

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

        last_updated = obs.get(
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
                f"Last Updated: {last_updated}",
                class_="last-update"
            )
        )

    # =================================================
    # PROBABILITY
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
    # CLINICAL FINDINGS
    # =================================================

    @output
    @render.ui
    def clinical_findings():

        obs = fhir_data().get("observation", {})

        f = factor_state()

        findings = [

            (
                "No Chills",
                f["no_chills"],
                "No chills reported"
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
                "No malignancy history"
            )
        ]

        cards = []

        for label, abnormal, value in findings:

            icon = "✓" if abnormal else "✗"

            cls = (
                "finding-item finding-positive"
                if abnormal else
                "finding-item finding-negative"
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
                            value,
                            class_="finding-value"
                        )
                    )
                )
            )

        return ui.div(*cards)

    # =================================================
    # DYNAMIC CLINICAL SUMMARY
    # =================================================

    @output
    @render.ui
    def clinical_summary():

        obs = fhir_data().get("observation", {})

        if "component" not in obs:

            return ui.div("No clinical data")

        rows = []

        for c in obs["component"]:

            code = c.get(
                "code",{}
            ).get(
                "coding",[{}]
            )[0].get("code")

            if code not in OBSERVATION_MAP:
                continue

            config = OBSERVATION_MAP[code]

            label = config["label"]

            unit = config["unit"]

            value = c.get(
                "valueQuantity",{}
            ).get("value")

            if value is None:
                continue

            display = f"{value} {unit}"

            # =========================================
            # COLOR LOGIC
            # =========================================

            css = "summary-value summary-normal"

            # Temperature

            if (
                code == "8310-5"
                and value < 36
            ):
                css = "summary-value summary-abnormal"

            # RBC

            elif (
                code == "789-8"
                and value < 4
            ):
                css = "summary-value summary-abnormal"

            # RDW

            elif (
                code == "788-0"
                and value > 14.5
            ):
                css = "summary-value summary-warning"

            rows.append(

                ui.tags.tr(

                    ui.tags.td(
                        label,
                        class_="summary-label"
                    ),

                    ui.tags.td(
                        display,
                        class_=css
                    )
                )
            )

        return ui.tags.table(

            {"class":"summary-table"},

            *rows
        )

# =====================================================
# APP
# =====================================================

app = App(app_ui, server)
