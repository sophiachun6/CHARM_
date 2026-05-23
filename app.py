from shiny import App, ui, render, reactive
import requests

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

    /* =================================================
       BODY
    ================================================= */

    body{
        background:#f3f6fb;
        font-family:Arial, Helvetica, sans-serif;
        padding:20px;
        color:#1f2937;
    }

    #token,#pid,#fhir,#obs{
        display:none !important;
    }

    /* =================================================
       TITLE
    ================================================= */

    .main-title{
        font-size:46px;
        font-weight:900;
        margin-bottom:6px;
        color:#0f172a;
    }

    .subtitle{
        color:#64748b;
        margin-bottom:28px;
        font-size:18px;
    }

    /* =================================================
       SIDEBAR
    ================================================= */

    .custom-sidebar{
        background:white;
        border-radius:22px;
        padding:24px;
        box-shadow:0 8px 24px rgba(0,0,0,.08);
    }

    /* =================================================
       CARD
    ================================================= */

    .card{
        background:white;
        border-radius:24px;
        padding:30px;
        margin-bottom:24px;
        box-shadow:0 8px 24px rgba(0,0,0,.08);
    }

    /* =================================================
       PATIENT HEADER
    ================================================= */

    .patient-header{
        background:linear-gradient(
            135deg,
            #2563eb,
            #1d4ed8
        );
        color:white;
        border-radius:24px;
        padding:32px;
        margin-bottom:24px;
        box-shadow:0 12px 28px rgba(0,0,0,.15);
    }

    .patient-name{
        font-size:36px;
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
        opacity:.8;
    }

    /* =================================================
       RISK
    ================================================= */

    .risk-center{
        text-align:center;
    }

    .risk-number{
        font-size:96px;
        font-weight:900;
        line-height:1;
        margin-top:10px;
        margin-bottom:12px;
    }

    .risk-label{
        font-size:26px;
        font-weight:800;
        margin-bottom:8px;
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
        margin-top:28px;
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

    /* =================================================
       AI NOTE
    ================================================= */

    .clinical-note{
        margin-top:24px;
        padding:20px;
        border-radius:18px;
        background:#f8fafc;
        color:#334155;
        font-size:15px;
        line-height:1.7;
    }

    /* =================================================
       FINDINGS
    ================================================= */

    .finding-item{
        border-radius:16px;
        padding:16px;
        margin-bottom:14px;
        display:flex;
        align-items:center;
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
    }

    .finding-value{
        margin-top:4px;
        font-size:13px;
        font-weight:500;
        opacity:.9;
    }

    /* =================================================
       SUMMARY TABLE
    ================================================= */

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
        color:#111827;
    }

    .summary-normal{
        color:#111827;
    }

    .summary-abnormal{
        color:#dc2626;
    }

    .summary-high{
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

        # -------------------------------------------------
        # SIDEBAR
        # -------------------------------------------------

        ui.sidebar(

            ui.div(

                {"class":"custom-sidebar"},

                ui.h4("Clinical Findings"),

                ui.hr(),

                ui.output_ui("clinical_findings")
            )
        ),

        # -------------------------------------------------
        # MAIN CONTENT
        # -------------------------------------------------

        ui.div(

            # =============================================
            # PATIENT HEADER
            # =============================================

            ui.div(

                {"class":"patient-header"},

                ui.output_ui("patient_header")
            ),

            # =============================================
            # RISK CARD
            # =============================================

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

            # =============================================
            # CLINICAL SUMMARY
            # =============================================

            ui.div(

                {"class":"card"},

                ui.h4("Clinical Summary"),

                ui.output_ui("clinical_summary")
            )
        )
    )
)

# =====================================================
# CHARM TABLE
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
    # EXTRACT LAB VALUES
    # =================================================

    @reactive.Calc
    def lab_values():

        obs = fhir_data().get("observation", {})

        result = {

            "temperature": None,
            "rbc": None,
            "rdw": None,
            "last_updated": "Unknown"
        }

        result["last_updated"] = obs.get(
            "lastUpdated",
            "Unknown"
        )

        if "component" not in obs:
            return result

        for c in obs["component"]:

            code = c.get(
                "code",{}
            ).get(
                "coding",[{}]
            )[0].get("code")

            # TEMPERATURE

            if code == "8310-5":

                result["temperature"] = c.get(
                    "valueQuantity",{}
                ).get("value")

            # RBC

            elif code == "789-8":

                result["rbc"] = c.get(
                    "valueQuantity",{}
                ).get("value")

            # RDW

            elif code == "788-0":

                result["rdw"] = c.get(
                    "valueQuantity",{}
                ).get("value")

        return result

    # =================================================
    # FACTOR STATE
    # =================================================

    @reactive.Calc
    def factor_state():

        labs = lab_values()

        return {

            "hypothermia":
            labs["temperature"] is not None
            and labs["temperature"] < 36,

            "anemia":
            labs["rbc"] is not None
            and labs["rbc"] < 4,

            "rdw":
            labs["rdw"] is not None
            and labs["rdw"] > 14.5
        }

    # =================================================
    # SCORE
    # =================================================

    def score():

        f = factor_state()

        return sum([

            f["hypothermia"],

            f["anemia"],

            f["rdw"]
        ])

    # =================================================
    # PATIENT HEADER
    # =================================================

    @output
    @render.ui
    def patient_header():

        data = fhir_data()

        patient = data.get("patient", {})

        labs = lab_values()

        try:

            family = patient["name"][0]["family"]

            given = patient["name"][0]["given"][0]

            fullname = f"{given} {family}"

        except:

            fullname = "Unknown Patient"

        gender = patient.get("gender", "Unknown")

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
                f"Last Updated: {labs['last_updated']}",
                class_="last-update"
            )
        )

    # =================================================
    # RISK NUMBER
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
    # AI NOTE
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

        labs = lab_values()

        f = factor_state()

        findings = [

            (
                "Hypothermia",
                f["hypothermia"],
                (
                    f"{labs['temperature']} °C"
                    if labs["temperature"] is not None
                    else "No data"
                )
            ),

            (
                "Anemia",
                f["anemia"],
                (
                    f"RBC {labs['rbc']}"
                    if labs["rbc"] is not None
                    else "No data"
                )
            ),

            (
                "RDW Elevation",
                f["rdw"],
                (
                    f"{labs['rdw']} %"
                    if labs["rdw"] is not None
                    else "No data"
                )
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

                        ui.div(
                            icon,
                            class_="finding-icon"
                        )
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
    # CLINICAL SUMMARY
    # =================================================

    @output
    @render.ui
    def clinical_summary():

        labs = lab_values()

        # ---------------------------------------------
        # TEMPERATURE
        # ---------------------------------------------

        temp = labs["temperature"]

        if temp is None:

            temp_text = "No data"
            temp_class = "summary-value"

        else:

            temp_text = f"{temp} °C"

            if temp < 36:

                temp_class = "summary-value summary-abnormal"

            else:

                temp_class = "summary-value summary-normal"

        # ---------------------------------------------
        # RBC
        # ---------------------------------------------

        rbc = labs["rbc"]

        if rbc is None:

            rbc_text = "No data"
            rbc_class = "summary-value"

        else:

            rbc_text = str(rbc)

            if rbc < 4:

                rbc_class = "summary-value summary-abnormal"

            else:

                rbc_class = "summary-value summary-normal"

        # ---------------------------------------------
        # RDW
        # ---------------------------------------------

        rdw = labs["rdw"]

        if rdw is None:

            rdw_text = "No data"
            rdw_class = "summary-value"

        else:

            rdw_text = f"{rdw} %"

            if rdw > 14.5:

                rdw_class = "summary-value summary-high"

            else:

                rdw_class = "summary-value summary-normal"

        return ui.tags.table(

            {"class":"summary-table"},

            # TEMPERATURE

            ui.tags.tr(

                ui.tags.td(
                    "Temperature",
                    class_="summary-label"
                ),

                ui.tags.td(
                    temp_text,
                    class_=temp_class
                )
            ),

            # RBC

            ui.tags.tr(

                ui.tags.td(
                    "RBC",
                    class_="summary-label"
                ),

                ui.tags.td(
                    rbc_text,
                    class_=rbc_class
                )
            ),

            # RDW

            ui.tags.tr(

                ui.tags.td(
                    "RDW",
                    class_="summary-label"
                ),

                ui.tags.td(
                    rdw_text,
                    class_=rdw_class
                )
            )
        )

# =====================================================
# APP
# =====================================================

app = App(app_ui, server)
