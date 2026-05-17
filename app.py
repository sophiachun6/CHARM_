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
          ["token","pid","fhir","obs"].forEach(k=>{
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

    body{
        background:linear-gradient(to bottom right,#eef2f7,#f9fbfd);
        font-family:Arial, Helvetica, sans-serif;
        padding:20px;
    }

    #token,#pid,#fhir,#obs{
        display:none !important;
    }

    /* =========================
       TITLE
    ========================== */

    .main-title{
        font-size:36px;
        font-weight:700;
        color:#1f2937;
        margin-bottom:5px;
    }

    .subtitle{
        color:#6b7280;
        margin-bottom:25px;
    }

    /* =========================
       CARD
    ========================== */

    .card{
        background:white;
        border-radius:18px;
        padding:24px;
        box-shadow:0 6px 18px rgba(0,0,0,.08);
        margin-bottom:20px;
        transition:.2s;
    }

    .card:hover{
        transform:translateY(-2px);
        box-shadow:0 10px 24px rgba(0,0,0,.12);
    }

    /* =========================
       SIDEBAR
    ========================== */

    .sidebar{
        background:white;
        border-radius:18px;
        padding:20px;
        box-shadow:0 6px 18px rgba(0,0,0,.08);
    }

    .sidebar h4{
        margin-bottom:20px;
    }

    /* =========================
       RISK
    ========================== */

    .risk-center{
        text-align:center;
    }

    .risk-number{
        font-size:72px;
        font-weight:800;
        line-height:1;
        margin-top:10px;
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

    .risk-label{
        font-size:22px;
        font-weight:700;
        margin-top:10px;
    }

    .risk-bar{
        height:16px;
        border-radius:999px;
        background:linear-gradient(
            to right,
            #43a047,
            #fdd835,
            #e53935
        );
        margin-top:25px;
        position:relative;
        overflow:hidden;
    }

    .risk-marker{
        position:absolute;
        top:-5px;
        width:4px;
        height:26px;
        background:black;
        border-radius:10px;
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
       FHIR
    ========================== */

    .fhir-box{
        max-height:300px;
        overflow:auto;
        background:#111827;
        color:#e5e7eb;
        border-radius:12px;
        padding:15px;
        font-size:13px;
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
    # Title
    # -------------------------------------------------
    ui.div(
        ui.div("CHARM Sepsis Mortality Predictor",
               class_="main-title"),

        ui.div(
            "AI-assisted in-hospital mortality risk estimation",
            class_="subtitle"
        )
    ),

    # -------------------------------------------------
    # Main Layout
    # -------------------------------------------------
    ui.layout_sidebar(

        # =========================
        # Sidebar
        # =========================
        ui.sidebar(

            ui.div(
                {"class":"sidebar"},

                ui.h4("Clinical Factors"),

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
                    "RDW",
                    {"No":"No","Yes":"Yes"},
                    inline=True
                ),

                ui.p("RDW > 14.5%"),

                ui.input_radio_buttons(
                    "malignancy",
                    "Malignancy",
                    {"No":"No","Yes":"Yes"},
                    inline=True
                ),

                ui.p("History of malignancy")
            )
        ),

        # =========================
        # Main Content
        # =========================
        ui.div(

            # -------------------------
            # Risk Card
            # -------------------------
            ui.div(
                {"class":"card risk-center"},

                ui.h3("Estimated Mortality Risk"),

                ui.output_ui("risk_label"),

                ui.output_ui("prob"),

                ui.output_ui("risk_bar"),

                ui.hr(),

                ui.h6("Reference"),

                ui.a(
                    "CHARM Score Research Paper",
                    href="https://www.ncbi.nlm.nih.gov/pubmed/?term=27832977",
                    target="_blank"
                ),

                ui.br(),
                ui.br(),

                ui.div(
                    "Produced by Dr. Chin-Chieh Wu"
                ),

                ui.div(
                    "SMART on FHIR UI by Howard"
                )
            ),

            # -------------------------
            # Factors Card
            # -------------------------
            ui.div(
                {"class":"card"},

                ui.h4("Contributing Clinical Factors"),

                ui.output_ui("factor_list")
            ),

            # -------------------------
            # FHIR Card
            # -------------------------
            ui.div(
                {"class":"card"},

                ui.h4("FHIR Patient & Observation Data"),

                ui.div(
                    {"class":"fhir-box"},
                    ui.tags.pre(
                        ui.output_text("patient_info")
                    )
                )
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
            input.token() and
            input.pid() and
            input.fhir()
        ):
            return {}

        headers = {
            "Authorization":
            f"Bearer {input.token()}",
            "Accept":"application/fhir+json"
        }

        data = {}

        data["patient"] = requests.get(
            f"{input.fhir()}/Patient/{input.pid()}",
            headers=headers,
            verify=False
        ).json()

        if input.obs():

            data["observation"] = requests.get(
                input.obs(),
                headers=headers,
                verify=False
            ).json()

        return data

    # -------------------------------------------------
    # SHOW FHIR JSON
    # -------------------------------------------------
    @output
    @render.text
    def patient_info():
        return json.dumps(
            fhir_data(),
            indent=2
        )

    # -------------------------------------------------
    # INIT UI FROM FHIR
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
    # LABEL
    # -------------------------------------------------
    @output
    @render.ui
    def risk_label():

        p = CHARM_TABLE.get(score(),0)

        if p<5:

            return ui.div(
                "VERY LOW RISK",
                class_="risk-label risk-low"
            )

        elif p<20:

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

        left = min(p/40*100,100)

        return ui.div(
            {"class":"risk-bar"},

            ui.div({
                "class":"risk-marker",
                "style":f"left:{left}%"
            })
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

            active = val=="Yes"

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

# =====================================================
# APP
# =====================================================
app = App(app_ui, server)
