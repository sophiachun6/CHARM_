from shiny import App, ui, render, reactive
import requests
import json
import urllib3
from datetime import datetime

# ==========================================================
# DEV ONLY
# ==========================================================
# In production:
# verify="/path/to/hospital_ca.pem"
# ==========================================================

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================================
# CHARM SCORE TABLE
# ==========================================================

CHARM_TABLE = {
    0: 0.36,
    1: 1.89,
    2: 5.79,
    3: 12.97,
    4: 23.58,
    5: 34.15
}

# ==========================================================
# OBSERVATION CONFIG
# ==========================================================

OBSERVATION_MAP = {

    "8310-5": {
        "label": "Temperature",
        "unit": "°C"
    },

    "789-8": {
        "label": "RBC",
        "unit": "M/uL"
    },

    "788-0": {
        "label": "RDW",
        "unit": "%"
    },

    "6690-2": {
        "label": "WBC",
        "unit": "K/uL"
    },

    "718-7": {
        "label": "Hemoglobin",
        "unit": "g/dL"
    },

    "777-3": {
        "label": "Platelet",
        "unit": "K/uL"
    },

    "8867-4": {
        "label": "Heart Rate",
        "unit": "bpm"
    },

    "9279-1": {
        "label": "Respiratory Rate",
        "unit": "/min"
    },

    "59408-5": {
        "label": "SpO2",
        "unit": "%"
    }
}

# ==========================================================
# UI
# ==========================================================

app_ui = ui.page_fluid(

    # ======================================================
    # URL HASH PARSER
    # ======================================================

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

    # ======================================================
    # CSS
    # ======================================================

    ui.tags.style("""

    body{
        background:#f1f5f9;
        font-family:Arial, Helvetica, sans-serif;
        padding:24px;
        color:#0f172a;
    }

    #token,#pid,#fhir,#obs{
        display:none !important;
    }

    .main-title{
        font-size:46px;
        font-weight:900;
        margin-bottom:6px;
    }

    .subtitle{
        font-size:18px;
        color:#64748b;
        margin-bottom:28px;
    }

    .card{
        background:white;
        border-radius:24px;
        padding:28px;
        margin-bottom:24px;
        box-shadow:0 8px 24px rgba(0,0,0,.08);
    }

    .sidebar-card{
        background:white;
        border-radius:24px;
        padding:24px;
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
        font-size:92px;
        font-weight:900;
        line-height:1;
        margin-top:14px;
        margin-bottom:16px;
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

    .risk-label{
        font-size:28px;
        font-weight:800;
        margin-bottom:12px;
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
        margin-top:26px;
        position:relative;
        overflow:hidden;
    }

    .risk-marker{
        position:absolute;
        top:-4px;
        width:6px;
        height:28px;
        background:black;
        border-radius:999px;
    }

    .clinical-note{
        margin-top:26px;
        padding:20px;
        border-radius:18px;
        background:#f8fafc;
        line-height:1.7;
        font-size:15px;
    }

    .finding-card{
        border-radius:18px;
        padding:16px;
        margin-bottom:14px;
        border:1px solid #e2e8f0;
    }

    .finding-positive{
        background:#fef2f2;
        border:1px solid #fecaca;
    }

    .finding-negative{
        background:#f0fdf4;
        border:1px solid #bbf7d0;
    }

    .finding-missing{
        background:#f8fafc;
        border:1px solid #cbd5e1;
    }

    .finding-title{
        font-weight:800;
        margin-bottom:6px;
    }

    .auto-tag{
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        font-size:12px;
        font-weight:700;
        margin-top:10px;
    }

    .auto-filled{
        background:#dbeafe;
        color:#1d4ed8;
    }

    .manual-edited{
        background:#fef3c7;
        color:#b45309;
    }

    .summary-table{
        width:100%;
        border-collapse:collapse;
    }

    .summary-table td{
        padding:18px;
        border-bottom:1px solid #e5e7eb;
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

    .warning-banner{
        background:#fff7ed;
        border:1px solid #fdba74;
        color:#9a3412;
        border-radius:18px;
        padding:18px;
        margin-bottom:22px;
        font-weight:700;
    }

    """),

    # ======================================================
    # HIDDEN INPUTS
    # ======================================================

    ui.input_text("token", ""),
    ui.input_text("pid", ""),
    ui.input_text("fhir", ""),
    ui.input_text("obs", ""),

    # ======================================================
    # TITLE
    # ======================================================

    ui.div(
        ui.div(
            "Predict In-hospital Mortality - CHARM Score",
            class_="main-title"
        ),

        ui.div(
            "AI-assisted sepsis mortality risk prediction with physician override support",
            class_="subtitle"
        )
    ),

    # ======================================================
    # MAIN LAYOUT
    # ======================================================

    ui.layout_sidebar(

        # ==================================================
        # SIDEBAR
        # ==================================================

        ui.sidebar(

            ui.div(

                {"class":"sidebar-card"},

                ui.h4("Clinical Assessment"),

                ui.hr(),

                ui.p(
                    "FHIR data will auto-populate below values. "
                    "Physicians may manually override based on clinical judgment."
                ),

                ui.input_radio_buttons(
                    "chills",
                    "No Chills",
                    {
                        "Unknown":"No Data",
                        "No":"No",
                        "Yes":"Yes"
                    },
                    selected="Unknown"
                ),

                ui.input_radio_buttons(
                    "hypothermia",
                    "Hypothermia (<36°C)",
                    {
                        "Unknown":"No Data",
                        "No":"No",
                        "Yes":"Yes"
                    },
                    selected="Unknown"
                ),

                ui.input_radio_buttons(
                    "anemia",
                    "Anemia (RBC < 4M/uL)",
                    {
                        "Unknown":"No Data",
                        "No":"No",
                        "Yes":"Yes"
                    },
                    selected="Unknown"
                ),

                ui.input_radio_buttons(
                    "rdw",
                    "RDW > 14.5%",
                    {
                        "Unknown":"No Data",
                        "No":"No",
                        "Yes":"Yes"
                    },
                    selected="Unknown"
                ),

                ui.input_radio_buttons(
                    "malignancy",
                    "Malignancy History",
                    {
                        "Unknown":"No Data",
                        "No":"No",
                        "Yes":"Yes"
                    },
                    selected="Unknown"
                ),

                ui.hr(),

                ui.output_ui("override_status")
            )
        ),

        # ==================================================
        # MAIN CONTENT
        # ==================================================

        ui.div(

            ui.output_ui("missing_warning"),

            # ==============================================
            # PATIENT HEADER
            # ==============================================

            ui.div(
                {"class":"patient-header"},
                ui.output_ui("patient_header")
            ),

            # ==============================================
            # RISK CARD
            # ==============================================

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
                    "Click here to see the reference",
                    href="https://pubmed.ncbi.nlm.nih.gov/27832977/",
                    target="_blank"
                ),

                ui.br(),
                ui.br(),

                ui.div("Produced by Dr. Chin-Chieh Wu"),
                ui.div("UI enhance and implement in SMART on FHIR by Howard")
            ),

           

            # ==============================================
            # SUMMARY
            # ==============================================

            ui.div(
                {"class":"card"},
                ui.h4("Clinical Summary"),
                ui.output_ui("clinical_summary")
            ),

            # ==============================================
            # RAW JSON
            # ==============================================

            ui.div(
                {"class":"card"},
                ui.tags.details(
                    ui.tags.summary("FHIR Raw JSON (click to expand)"),
                    ui.tags.pre(ui.output_text("patient_json"))
                )
            )
        )
    )
)

# ==========================================================
# SERVER
# ==========================================================

def server(input, output, session):

    @reactive.Calc
    def fhir_data():

        if not (
            input.token()
            and input.pid()
            and input.fhir()
        ):
            return {}

        headers = {
            "Authorization": f"Bearer {input.token()}",
            "Accept": "application/fhir+json"
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

    @output
    @render.text
    def patient_json():
        return json.dumps(fhir_data(), indent=2)

    @reactive.Effect
    def init_ui_from_fhir():

        obs = fhir_data().get("observation")

        if not obs or "component" not in obs:
            return

        defaults = {
            "chills": "Unknown",
            "hypothermia": "Unknown",
            "anemia": "Unknown",
            "rdw": "Unknown",
            "malignancy": "Unknown"
        }

        for c in obs["component"]:

            code = c.get(
                "code", {}
            ).get(
                "coding", [{}]
            )[0].get("code")

            # chills
            if code == "chills":
            
                if c.get("valueBoolean") is True:
                    defaults["chills"] = "Yes"
            
                elif c.get("valueBoolean") is False:
                    defaults["chills"] = "No"
            
            # malignancy
            elif code == "malignancy":
            
                if c.get("valueBoolean") is True:
                    defaults["malignancy"] = "Yes"
            
                elif c.get("valueBoolean") is False:
                    defaults["malignancy"] = "No"

            elif code == "789-8":

                value = c.get(
                    "valueQuantity", {}
                ).get("value")

                if value is not None:
                    defaults["anemia"] = (
                        "Yes" if value < 4 else "No"
                    )

            elif code == "788-0":

                value = c.get(
                    "valueQuantity", {}
                ).get("value")

                if value is not None:
                    defaults["rdw"] = (
                        "Yes" if value > 14.5 else "No"
                    )

            elif code == "8310-5":

                value = c.get(
                    "valueQuantity", {}
                ).get("value")

                if value is not None:
                    defaults["hypothermia"] = (
                        "Yes" if value < 36 else "No"
                    )

        for k, v in defaults.items():
            session.send_input_message(k, {"value": v})

    def score():

        return sum([
            input.chills() == "Yes",
            input.hypothermia() == "Yes",
            input.anemia() == "Yes",
            input.rdw() == "Yes",
            input.malignancy() == "Yes",
        ])

    def has_missing_data():

        return any([
            input.chills() == "Unknown",
            input.hypothermia() == "Unknown",
            input.anemia() == "Unknown",
            input.rdw() == "Unknown",
            input.malignancy() == "Unknown",
        ])

    @output
    @render.ui
    def missing_warning():

        if not has_missing_data():
            return ui.div()

        return ui.div(
            "Incomplete clinical data detected. "
            "Some factors contain 'No Data'. "
            "Clinical interpretation should be performed with caution.",
            class_="warning-banner"
        )

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
            datetime.now().strftime("%Y-%m-%d %H:%M")
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

    @output
    @render.ui
    def prob():

        p = CHARM_TABLE.get(score(), 0)

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

    @output
    @render.ui
    def risk_label():

        p = CHARM_TABLE.get(score(), 0)

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

    @output
    @render.ui
    def risk_bar():

        p = CHARM_TABLE.get(score(), 0)

        left = min(p / 40 * 100, 100)

        return ui.div(

            {"class":"risk-bar"},

            ui.div({
                "class":"risk-marker",
                "style":f"left:{left}%"
            })
        )

    @output
    @render.ui
    def clinical_note():

        p = CHARM_TABLE.get(score(), 0)

        if has_missing_data():

            note = (
                "Incomplete clinical information detected. "
                "Interpret CHARM score carefully and confirm missing findings manually."
            )

        elif p < 5:

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

    @output
    @render.ui
    def override_status():

        return ui.div(

            ui.div(
                "Auto-filled from EHR",
                class_="auto-tag auto-filled"
            ),

            ui.br(),

            ui.div(
                "Physician editable",
                class_="auto-tag manual-edited"
            )
        )

    

    @output
    @render.ui
    def clinical_summary():

        obs = fhir_data().get("observation", {})

        if "component" not in obs:
            return ui.div("No clinical data available")

        rows = []

        for c in obs["component"]:

            code = c.get(
                "code", {}
            ).get(
                "coding", [{}]
            )[0].get("code")

            if code not in OBSERVATION_MAP:
                continue

            config = OBSERVATION_MAP[code]

            label = config["label"]
            unit = config["unit"]

            value = c.get(
                "valueQuantity", {}
            ).get("value")

            if value is None:
                continue

            display = f"{value} {unit}"

            css = "summary-value summary-normal"

            if (
                code == "8310-5"
                and value < 36
            ):
                css = "summary-value summary-abnormal"

            elif (
                code == "789-8"
                and value < 4
            ):
                css = "summary-value summary-abnormal"

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

# ==========================================================
# APP
# ==========================================================

app = App(app_ui, server)
