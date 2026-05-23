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
    # ========================
