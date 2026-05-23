from shiny import App, ui, render, reactive
import requests
import json
import urllib3

# 停用因為 verify=False 產生的 InsecureRequestWarning 警告 (僅限測試環境)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================
# 全域環境設定 (GLOBAL CONFIG)
# =====================================================
# TODO: 若部署至醫院正式環境 (Production)，請務必將此設為 True，並配置對應的 CA 憑證
VERIFY_SSL = False  

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
# OBSERVATION MAP (用於全局生命徵象摘要表)
# =====================================================
OBSERVATION_MAP = {
    "8310-5": {"label": "Temperature", "unit": "°C"},
    "789-8": {"label": "RBC", "unit": ""},
    "788-0": {"label": "RDW", "unit": "%"},
    "6690-2": {"label": "WBC", "unit": "K/uL"},
    "718-7": {"label": "Hemoglobin", "unit": "g/dL"},
    "777-3": {"label": "Platelet", "unit": "K/uL"},
    "8867-4": {"label": "Heart Rate", "unit": "bpm"},
    "9279-1": {"label": "Respiratory Rate", "unit": "/min"},
    "59408-5": {"label": "SpO2", "unit": "%"}
}

# =====================================================
# UI
# =====================================================
app_ui = ui.page_fluid(

    # -------------------------------------------------
    # URL HASH → SHINY INPUT
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
    # CSS (V1 高級儀表板樣式 + 新增側邊欄樣式)
    # -------------------------------------------------
    ui.tags.style("""
    body{ background:#f3f6fb; font-family:Arial, Helvetica, sans-serif; padding:20px; color:#1f2937; }
    #token,#pid,#fhir,#obs{ display:none !important; }
    .main-title{ font-size:48px; font-weight:900; margin-bottom:6px; color:#0f172a; }
    .subtitle{ color:#64748b; margin-bottom:28px; font-size:18px; }
    .custom-sidebar{ background:white; border-radius:24px; padding:24px; box-shadow:0 8px 24px rgba(0,0,0,.08); }
    .card{ background:white; border-radius:24px; padding:30px; margin-bottom:24px; box-shadow:0 8px 24px rgba(0,0,0,.08); }
    .patient-header{ background:linear-gradient(135deg, #2563eb, #1d4ed8); color:white; border-radius:24px; padding:34px; margin-bottom:24px; box-shadow:0 12px 28px rgba(0,0,0,.15); }
    .patient-name{ font-size:38px; font-weight:900; margin-bottom:10px; }
    .patient-meta{ font-size:16px; opacity:.92; }
    .last-update{ margin-top:12px; font-size:14px; opacity:.82; }
    .risk-center{ text-align:center; }
    .risk-number{ font-size:100px; font-weight:900; line-height:1; margin-top:10px; margin-bottom:14px; }
    .risk-label{ font-size:28px; font-weight:800; margin-bottom:10px; }
    .risk-low{ color:#16a34a; }
    .risk-mid{ color:#f59e0b; }
    .risk-high{ color:#dc2626; }
    .risk-bar{ height:20px; border-radius:999px; background:linear-gradient(to right, #22c55e, #eab308, #ef4444); margin-top:30px; position:relative; overflow:hidden; }
    .risk-marker{ position:absolute; top:-5px; width:6px; height:30px; background:black; border-radius:999px; }
    .clinical-note{ margin-top:26px; padding:20px; border-radius:18px; background:#f8fafc; color:#334155; font-size:15px; line-height:1.7; font-weight:600;}
    .summary-table{ width:100%; border-collapse:collapse; }
    .summary-table td{ padding:18px; border-bottom:1px solid #e5e7eb; font-size:15px; }
    .summary-label{ width:40%; color:#64748b; font-weight:700; }
    .summary-value{ font-weight:800; }
    .summary-normal{ color:#111827; }
    .summary-abnormal{ color:#dc2626; }
    .summary-warning{ color:#ea580c; }
    .alert-box{ background:#fffbeb; color:#b45309; border:1px solid #fde68a; padding:12px; border-radius:12px; font-size:13px; margin-bottom:20px; font-weight:600;}
    .override-label{ font-size: 14px; color: #64748b; margin-bottom: 20px;}
    """),

    # -------------------------------------------------
    # HIDDEN INPUTS
    # -------------------------------------------------
    ui.input_text("token",""),
    ui.input_text("pid",""),
    ui.input_text("fhir",""),
    ui.input_text("obs",""),

    # -------------------------------------------------
    # TITLE
    # -------------------------------------------------
    ui.div(
        ui.div("CHARM Sepsis Mortality Predictor", class_="main-title"),
        ui.div("AI-assisted in-hospital mortality risk estimation (with CDSS Override)", class_="subtitle")
    ),

    # -------------------------------------------------
    # MAIN LAYOUT
    # -------------------------------------------------
    ui.layout_sidebar(

        # =============================================
        # SIDEBAR (Interactive & Override-able)
        # =============================================
        ui.sidebar(
            ui.div(
                {"class":"custom-sidebar"},
                ui.h4("Clinical Factors"),
                ui.p("Auto-populated from EHR. Adjust manually if needed.", class_="override-label"),
                
                # 缺失資料警告區塊
                ui.output_ui("missing_data_alert"),

                ui.hr(),

                ui.input_radio_buttons("chills", "Absence of Chills (無發冷)", {"No":"No","Yes":"Yes"}, inline=True),
                ui.input_radio_buttons("hypothermia", "Hypothermia (< 36°C)", {"No":"No","Yes":"Yes"}, inline=True),
                ui.input_radio_buttons("anemia", "Anemia (RBC < 4M/uL)", {"No":"No","Yes":"Yes"}, inline=True),
                ui.input_radio_buttons("rdw", "RDW > 14.5%", {"No":"No","Yes":"Yes"}, inline=True),
                ui.input_radio_buttons("malignancy", "Malignancy History", {"No":"No","Yes":"Yes"}, inline=True)
            )
        ),

        # =============================================
        # MAIN CONTENT
        # =============================================
        ui.div(
            # PATIENT HEADER
            ui.div(
                {"class":"patient-header"},
                ui.output_ui("patient_header")
            ),

            # RISK CARD
            ui.div(
                {"class":"card risk-center"},
                ui.h3("Estimated In-hospital Mortality Risk"),
                ui.output_ui("risk_label"),
                ui.output_ui("prob"),
                ui.output_ui("risk_bar"),
                ui.output_ui("clinical_note"),
                ui.hr(),
                ui.div(
                    ui.a("Reference: CHARM Score Research Paper", href="https://pubmed.ncbi.nlm.nih.gov/27832977/", target="_blank"),
                    style="margin-bottom:10px; font-size:14px;"
                ),
                ui.div("Produced by Dr. Chin-Chieh Wu | UI by Howard | CDSS Optimized", style="font-size:13px; color:#94a3b8;")
            ),

            # CLINICAL SUMMARY (All Vitals)
            ui.div(
                {"class":"card"},
                ui.h4("Global Clinical Summary"),
                ui.p("Other vitals and labs from current encounter:", style="color:#64748b; font-size:14px;"),
                ui.output_ui("clinical_summary")
            )
        )
    )
)

# =====================================================
# SERVER
# =====================================================
def server(input, output, session):

    # -------------------------------------------------
    # FETCH FHIR DATA (With Error Handling)
    # -------------------------------------------------
    @reactive.Calc
    def fhir_data():
        if not (input.token() and input.pid() and input.fhir()):
            return {}

        headers = {
            "Authorization": f"Bearer {input.token()}",
            "Accept": "application/fhir+json"
        }
        
        data = {"found_codes": []}

        try:
            # Fetch Patient
            patient_res = requests.get(
                f"{input.fhir()}/Patient/{input.pid()}",
                headers=headers, verify=VERIFY_SSL, timeout=10
            )
            data["patient"] = patient_res.json()

            # Fetch Observation
            if input.obs():
                obs_res = requests.get(
                    input.obs(),
                    headers=headers, verify=VERIFY_SSL, timeout=10
                )
                data["observation"] = obs_res.json()
                
                # 紀錄成功抓取到的檢驗項目碼，用於偵測缺失資料
                if "component" in data["observation"]:
                    for c in data["observation"]["component"]:
                        code = c.get("code", {}).get("coding", [{}])[0].get("code")
                        if code:
                            data["found_codes"].append(code)

        except Exception as e:
            data["error"] = str(e)

        return data

    # -------------------------------------------------
    # AUTO-POPULATE UI & CHECK MISSING DATA
    # -------------------------------------------------
    missing_fields_state = reactive.Value([])

    @reactive.Effect
    def init_ui_from_fhir():
        obs = fhir_data().get("observation", {})
        found_codes = fhir_data().get("found_codes", [])
        
        if not obs or "component" not in obs:
            return

        defaults = {
            "chills": "No",
            "hypothermia": "No",
            "anemia": "No",
            "rdw": "No",
            "malignancy": "No"
        }

        # 根據 FHIR Data 設定數值
        for c in obs["component"]:
            code = c.get("code", {}).get("coding", [{}])[0].get("code")
            val = c.get("valueQuantity", {}).get("value")
            val_int = c.get("valueInteger")

            if code == "chills" and val_int == 1: defaults["chills"] = "Yes"
            if code == "malignancy" and val_int == 1: defaults["malignancy"] = "Yes"
            if code == "789-8" and val is not None and val < 4: defaults["anemia"] = "Yes"
            if code == "788-0" and val is not None and val > 14.5: defaults["rdw"] = "Yes"
            if code == "8310-5" and val is not None and val < 36: defaults["hypothermia"] = "Yes"

        # 更新 UI Radio Buttons
        ui.update_radio_buttons("chills", selected=defaults["chills"])
        ui.update_radio_buttons("hypothermia", selected=defaults["hypothermia"])
        ui.update_radio_buttons("anemia", selected=defaults["anemia"])
        ui.update_radio_buttons("rdw", selected=defaults["rdw"])
        ui.update_radio_buttons("malignancy", selected=defaults["malignancy"])

        # 檢查是否有缺失的關鍵判斷資料
        missing = []
        if "chills" not in found_codes: missing.append("Chills")
        if "8310-5" not in found_codes: missing.append("Temperature")
        if "789-8" not in found_codes: missing.append("RBC")
        if "788-0" not in found_codes: missing.append("RDW")
        if "malignancy" not in found_codes: missing.append("Malignancy")
        
        missing_fields_state.set(missing)

    # -------------------------------------------------
    # MISSING DATA ALERT UI
    # -------------------------------------------------
    @output
    @render.ui
    def missing_data_alert():
        missing = missing_fields_state.get()
        if not missing:
            return None
        
        missing_str = ", ".join(missing)
        return ui.div(
            ui.span("⚠️ Incomplete EHR Data: "),
            ui.span(f"Could not find values for {missing_str}. Defaulted to 'No'. Please review manually."),
            class_="alert-box"
        )

    # -------------------------------------------------
    # REACTIVE SCORE CALCULATION
    # -------------------------------------------------
    @reactive.Calc
    def score():
        # 等待 UI 初始化
        if not input.chills(): 
            return 0
            
        return sum([
            input.chills() == "Yes",
            input.hypothermia() == "Yes",
            input.anemia() == "Yes",
            input.rdw() == "Yes",
            input.malignancy() == "Yes"
        ])

    # -------------------------------------------------
    # PATIENT HEADER
    # -------------------------------------------------
    @output
    @render.ui
    def patient_header():
        data = fhir_data()
        patient = data.get("patient", {})
        obs = data.get("observation", {})
        error = data.get("error")

        if error:
            return ui.div(ui.div("Error connecting to FHIR Server", class_="patient-name"), ui.div(error, class_="patient-meta"))

        try:
            family = patient["name"][0]["family"]
            given = patient["name"][0]["given"][0]
            fullname = f"{given} {family}"
        except:
            fullname = "Waiting for Patient Data..."

        gender = patient.get("gender", "Unknown")
        last_updated = obs.get("lastUpdated", "Unknown")

        return ui.div(
            ui.div(fullname, class_="patient-name"),
            ui.div(f"Patient ID: {input.pid() or '--'} • Gender: {gender}", class_="patient-meta"),
            ui.div(f"Last Updated: {last_updated}", class_="last-update")
        )

    # -------------------------------------------------
    # PROBABILITY
    # -------------------------------------------------
    @output
    @render.ui
    def prob():
        p = CHARM_TABLE.get(score(), 0)
        cls = "risk-low" if p < 5 else "risk-mid" if p < 20 else "risk-high"
        return ui.div(f"{p:.2f}%", class_=f"risk-number {cls}")

    # -------------------------------------------------
    # RISK LABEL
    # -------------------------------------------------
    @output
    @render.ui
    def risk_label():
        p = CHARM_TABLE.get(score(), 0)
        if p < 5: return ui.div("VERY LOW RISK", class_="risk-label risk-low")
        elif p < 20: return ui.div("MODERATE RISK", class_="risk-label risk-mid")
        else: return ui.div("HIGH RISK", class_="risk-label risk-high")

    # -------------------------------------------------
    # RISK BAR
    # -------------------------------------------------
    @output
    @render.ui
    def risk_bar():
        p = CHARM_TABLE.get(score(), 0)
        left = min(p / 40 * 100, 100)
        return ui.div(
            {"class":"risk-bar"},
            ui.div({"class":"risk-marker", "style":f"left:{left}%"})
        )

    # -------------------------------------------------
    # CLINICAL NOTE
    # -------------------------------------------------
    @output
    @render.ui
    def clinical_note():
        p = CHARM_TABLE.get(score(), 0)
        if p < 5:
            note = "Patient currently demonstrates low mortality risk. Continue routine monitoring and standard care."
        elif p < 20:
            note = "Moderate mortality risk detected. Recommend closer observation and repeat laboratory evaluation."
        else:
            note = "High mortality risk detected. Consider ICU evaluation and urgent clinical escalation."
        
        return ui.div(note, class_="clinical-note")

    # -------------------------------------------------
    # DYNAMIC CLINICAL SUMMARY
    # -------------------------------------------------
    @output
    @render.ui
    def clinical_summary():
        obs = fhir_data().get("observation", {})
        if "component" not in obs:
            return ui.div("No global clinical data available from this observation.", style="color:#64748b; font-style:italic;")

        rows = []
        for c in obs["component"]:
            code = c.get("code", {}).get("coding", [{}])[0].get("code")
            if code not in OBSERVATION_MAP: continue

            config = OBSERVATION_MAP[code]
            label = config["label"]
            unit = config["unit"]
            value = c.get("valueQuantity", {}).get("value")

            if value is None: continue
            display = f"{value} {unit}"

            css = "summary-value summary-normal"
            if code == "8310-5" and value < 36: css = "summary-value summary-abnormal"
            elif code == "789-8" and value < 4: css = "summary-value summary-abnormal"
            elif code == "788-0" and value > 14.5: css = "summary-value summary-warning"

            rows.append(
                ui.tags.tr(
                    ui.tags.td(label, class_="summary-label"),
                    ui.tags.td(display, class_=css)
                )
            )

        if not rows:
             return ui.div("No matching vital signs found.", style="color:#64748b;")

        return ui.tags.table({"class":"summary-table"}, *rows)

# =====================================================
# APP INSTANCE
# =====================================================
app = App(app_ui, server)
