from shiny import App, ui, render, reactive
import requests
import json

# =====================================================
# UI
# =====================================================
app_ui = ui.page_fluid(

    # -------------------------------------------------
    # URL hash → Shiny input
    # -------------------------------------------------
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

    # -------------------------------------------------
    # CSS
    # -------------------------------------------------
    ui.tags.style("""

    /* =========================
       BODY
    ========================== */

    body{
        background:#f4f7fb;
        font-family:Arial, Helvetica, sans-serif;
        padding:20px;
        color:#1f2937;
    }

    #token,#pid,#fhir,#obs{
        display:none !important;
    }

    /* =========================
       TITLE
    ========================== */

    .main-title{
        font-size:42px;
        font-weight:800;
        margin-bottom:6px;
        color:#111827;
    }

    .subtitle{
        color:#6b7280;
        margin-bottom:28px;
        font-size:17px;
    }

    /* =========================
       CUSTOM SIDEBAR
    ========================== */

    .custom-sidebar{
        background:white;
        border-radius:20px;
        padding:24px;
        box-shadow:0 6px 18px rgba(0,0,0,.08);
    }

    /* =========================
       CARD
    ========================== */

    .card{
        background:white;
        border-radius:22px;
        padding:28px;
        margin-bottom:24px;
        box-shadow:0 6px 18px rgba(0,0,0,.08);
        transition:.2s;
    }

    .card:hover{
        transform:translateY(-2px);
        box-shadow:0 10px 24px rgba(0,0,0,.12);
    }

    /* =========================
       PATIENT HEADER
    ========================== */

    .patient-header{
        background:linear-gradient(
            135deg,
            #2563eb,
            #1e40af
        );
        color:white;
        border-radius:22px;
        padding:30px;
        margin-bottom:24px;
        box-shadow:0 10px 24px rgba(0,0,0,.15);
    }

    .patient-name{
        font-size:32px;
        font-weight:800;
        margin-bottom:8px;
    }

    .patient-meta{
        font-size:16px;
        opacity:.9;
    }

    /* =========================
       RISK
    ========================== */

    .risk-center{
        text-align:center;
    }

    .risk-number{
        font-size:88px;
        font-weight:800;
        line-height:1;
        margin-top:12px;
        margin-bottom:12px;
    }

    .risk-label{
        font-size:24px;
        font-weight:700;
        margin-bottom:8px;
    }

    .risk-low{
        color:#43a047;
    }

    .risk-mid{
        color:#fb8c00;
    }

    .risk-high{
        color:#e53935;
    }

    .risk-bar{
        height:18px;
        border-radius:999px;
        background:linear-gradient(
            to right,
            #43a047,
            #fdd835,
            #e53935
        );
        margin-top:28px;
        position:relative;
        overflow:hidden;
    }

    .risk-marker{
        position:absolute;
        top:-5px;
        width:5px;
        height:28px;
        background:black;
        border-radius:10px;
    }

    .clinical-note{
        margin-top:22px;
        padding:16px;
        background:#f8fafc;
        border-radius:14px;
        font-size:15px;
        color:#374151;
    }

    /* =========================
       FACTORS
    ========================== */

    .factor-pill{
        display:inline-block;
        padding:10px 18px;
        border-radius:999px;
        margin:6px;
        font-weight:600;
        font-size:15px;
    }

    .pill-active{
        background:#ffebee;
        color:#c62828;
    }

    .pill-inactive{
        background:#eceff1;
        color:#607d8b;
    }

    /* =========================
       SUMMARY TABLE
    ========================== */

    .summary-table{
        width:100%;
        border-collapse:collapse;
    }

    .summary-table td{
        padding:14px;
        border-bottom:1px solid #e5e7eb;
        font-size:15px;
    }

    .summary-label{
        color:#6b7280;
        width:40%;
        font-weight:600;
    }

    .summary-value{
        font-weight:700;
        color:#111827;
    }

    .abnormal{
        color:#dc2626;
    }

    /* =========================
       RADIO BUTTON SPACING
    ========================== */

    .form-check{
        margin-right:18px;
    }

    """),

    # -------------------------------------------------
    # Hidden inputs
    # -------------------------------------------------
    ui.input_text("token",""),
    ui.input_text("pid",""),
    ui.input_text("fhir",""),
    ui.input_text("obs",""),

    # -------------------------------------------------
    # TITLE
    # -------------------------------------------------
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

    # -------------------------------------------------
    # MAIN LAYOUT
    # -------------------------------------------------
    ui.layout_sidebar(

        # =================================================
        # SIDEBAR
        # =================================================
        ui.sidebar(

            ui.div(

                {"class":"custom-sidebar"},

                ui.h4("Clinical Factors"),

                ui.hr(),

                ui.input_radio_buttons(
                    "chills",
                    "No Chills",
                    {"No":"No","Yes":"Yes"},
                    inline=True
                ),

                ui.input_radio_buttons(
                    "hypothermia",
                    "Hypothermia",
                    {"No":"No","Yes":"Yes"},
                    inline=True
                ),

                ui.p("Temperature < 36°C"),

                ui.input_radio_buttons(
                    "anemia",
                    "Anemia",
                    {"No":"No","Yes":"Yes"},
                    inline=True
                ),

                ui.p("RBC < 4M/uL"),

                ui.input_radio_buttons(
                    "rdw",
                    "RDW > 14.5%",
                    {"No":"No","Yes":"Yes"},
                    inline=True
                ),

                ui.input_radio_buttons(
                    "malignancy",
                    "Malignancy",
                    {"No":"No","Yes":"Yes"},
                    inline=True
                ),

                ui.p("History of malignancy")
            )
        ),

        # =================================================
        # MAIN CONTENT
        # =================================================
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
                    href="https://www.ncbi.nlm.nih.gov/pubmed/?term=27832977",
                    target="_blank"
                ),

                ui.br(),
                ui.br(),

                ui.div("Produced by Dr. Chin-Chieh Wu"),

                ui.div("SMART on FHIR UI by Howard")
            ),

            # =============================================
            # FACTORS CARD
            # =============================================
            ui.div(

                {"class":"card"},

                ui.h4("Contributing Clinical Factors"),

                ui.output_ui("factor_list")
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

    # -------------------------------------------------
    # FHIR FETCH
    # -------------------------------------------------
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
            "Accept":"application/fhir+json"
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

    # -------------------------------------------------
    # INIT FROM FHIR
    # -------------------------------------------------
    @reactive.Effect
    def init_ui_from_fhir():

        obs = fhir_data().get("observation")

        if not obs or "component" not in obs:
            return

        defaults = {

            "chills":"No",
            "hypothermia":"No",
            "anemia":"No",
            "rdw":"No",
            "malignancy":"No"
        }

        for c in obs["component"]:

            code = c.get(
                "code",{}
            ).get(
                "coding",[{}]
            )[0].get("code")

            if (
                code=="chills"
                and c.get("valueInteger")==1
            ):
                defaults["chills"]="Yes"

            elif (
                code=="malignancy"
                and c.get("valueInteger")==1
            ):
                defaults["malignancy"]="Yes"

            elif (
                code=="789-8"
                and c.get(
                    "valueQuantity",{}
                ).get("value",999)<4
            ):
                defaults["anemia"]="Yes"

            elif (
                code=="788-0"
                and c.get(
                    "valueQuantity",{}
                ).get("value",0)>14.5
            ):
                defaults["rdw"]="Yes"

            elif (
                code=="8310-5"
                and c.get(
                    "valueQuantity",{}
                ).get("value",99)<36
            ):
                defaults["hypothermia"]="Yes"

        for k,v in defaults.items():

            session.send_input_message(
                k,
                {"value":v}
            )

    # -------------------------------------------------
    # SCORE
    # -------------------------------------------------
    def score():

        return sum([

            input.chills()=="Yes",

            input.hypothermia()=="Yes",

            input.anemia()=="Yes",

            input.rdw()=="Yes",

            input.malignancy()=="Yes"
        ])

    # -------------------------------------------------
    # PATIENT HEADER
    # -------------------------------------------------
    @output
    @render.ui
    def patient_header():

        data = fhir_data()
        patient = data.get("patient", {})

        try:
            family = patient["name"][0]["family"]
            given = patient["name"][0]["given"][0]
            fullname = f"{given} {family}"
        except:
            fullname = "Unknown Patient"

        gender = patient.get("gender", "Unknown")

        patient_id = input.pid()

        return ui.div(

            ui.div(
                fullname,
                class_="patient-name"
            ),

            ui.div(
                f"Patient ID: {patient_id} • Gender: {gender}",
                class_="patient-meta"
            )
        )

    # -------------------------------------------------
    # PROBABILITY
    # -------------------------------------------------
    @output
    @render.ui
    def prob():

        p = CHARM_TABLE.get(score(),0)

        cls = (
            "risk-low"
            if p<5 else
            "risk-mid"
            if p<20 else
            "risk-high"
        )

        return ui.div(
            f"{p:.2f}%",
            class_=f"risk-number {cls}"
        )

    # -------------------------------------------------
    # RISK LABEL
    # -------------------------------------------------
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

    # -------------------------------------------------
    # RISK BAR
    # -------------------------------------------------
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

    # -------------------------------------------------
    # CLINICAL NOTE
    # -------------------------------------------------
    @output
    @render.ui
    def clinical_note():

        p = CHARM_TABLE.get(score(),0)

        if p < 5:
            note = (
                "Patient currently demonstrates low mortality risk. "
                "Continue standard monitoring."
            )

        elif p < 20:
            note = (
                "Moderate mortality risk detected. "
                "Recommend close monitoring and repeat laboratory evaluation."
            )

        else:
            note = (
                "High mortality risk detected. "
                "Immediate clinical attention and escalation recommended."
            )

        return ui.div(
            note,
            class_="clinical-note"
        )

    # -------------------------------------------------
    # FACTOR LIST
    # -------------------------------------------------
    @output
    @render.ui
    def factor_list():

        factors = [

            ("No Chills", input.chills()),

            ("Hypothermia", input.hypothermia()),

            ("Anemia", input.anemia()),

            ("RDW > 14.5%", input.rdw()),

            ("Malignancy", input.malignancy())
        ]

        pills = []

        for label,val in factors:

            active = val == "Yes"

            pills.append(

                ui.span(

                    label,

                    class_=(
                        "factor-pill pill-active"
                        if active else
                        "factor-pill pill-inactive"
                    )
                )
            )

        return ui.div(*pills)

    # -------------------------------------------------
    # CLINICAL SUMMARY
    # -------------------------------------------------
    @output
    @render.ui
    def clinical_summary():

        data = fhir_data()

        obs = data.get("observation", {})

        temp = "N/A"
        rbc = "N/A"
        rdw = "N/A"

        if "component" in obs:

            for c in obs["component"]:

                code = c.get(
                    "code",{}
                ).get(
                    "coding",[{}]
                )[0].get("code")

                # Temperature
                if code == "8310-5":

                    value = c.get(
                        "valueQuantity",{}
                    ).get("value","N/A")

                    temp = f"{value} °C"

                # RBC
                elif code == "789-8":

                    value = c.get(
                        "valueQuantity",{}
                    ).get("value","N/A")

                    rbc = str(value)

                # RDW
                elif code == "788-0":

                    value = c.get(
                        "valueQuantity",{}
                    ).get("value","N/A")

                    rdw = f"{value} %"

        return ui.tags.table(

            {"class":"summary-table"},

            ui.tags.tr(
                ui.tags.td(
                    "Temperature",
                    class_="summary-label"
                ),
                ui.tags.td(
                    temp,
                    class_="summary-value abnormal"
                )
            ),

            ui.tags.tr(
                ui.tags.td(
                    "RBC",
                    class_="summary-label"
                ),
                ui.tags.td(
                    rbc,
                    class_="summary-value abnormal"
                )
            ),

            ui.tags.tr(
                ui.tags.td(
                    "RDW",
                    class_="summary-label"
                ),
                ui.tags.td(
                    rdw,
                    class_="summary-value abnormal"
                )
            ),

            ui.tags.tr(
                ui.tags.td(
                    "Malignancy History",
                    class_="summary-label"
                ),
                ui.tags.td(
                    input.malignancy(),
                    class_="summary-value"
                )
            )
        )

# =====================================================
# APP
# =====================================================
app = App(app_ui, server)
