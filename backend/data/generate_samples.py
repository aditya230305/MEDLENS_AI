"""
Sample Medical Report Generator
Creates realistic clinical PDF and text reports for instant one-click viva demonstration.
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_reports"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def build_pdf_report(filename: str, title: str, patient_info: dict, tests_data: list, notes: list):
    pdf_path = SAMPLE_DIR / filename
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1
    )
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#475569"),
        alignment=1
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e40af"),
        spaceBefore=10,
        spaceAfter=5
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )
    cell_bold_flag = ParagraphStyle(
        'CellBoldFlag',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#dc2626"),
        fontName="Helvetica-Bold"
    )

    elements = []

    # Hospital / Lab Header
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph("NABH & NABL ACCREDITED DIAGNOSTIC MOLECULAR PATHOLOGY LABORATORY", sub_title_style))
    elements.append(Paragraph("108 Medical Center Boulevard, Tech Health City • Phone: (800) 555-LABS", sub_title_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=10))

    # Patient Demographic Box
    patient_table_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient_info['name']}", cell_style),
            Paragraph(f"<b>Patient ID:</b> {patient_info['id']}", cell_style),
            Paragraph(f"<b>Age / Gender:</b> {patient_info['age']} / {patient_info['gender']}", cell_style)
        ],
        [
            Paragraph(f"<b>Referred By:</b> {patient_info['doctor']}", cell_style),
            Paragraph(f"<b>Collection Date:</b> {patient_info['date']}", cell_style),
            Paragraph(f"<b>Report Date:</b> {patient_info['date']}", cell_style)
        ]
    ]
    p_table = Table(patient_table_data, colWidths=[2.5*inch, 2.2*inch, 2.3*inch])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 15))

    # Test Results Table
    elements.append(Paragraph("LABORATORY TEST RESULTS", section_style))

    table_data = [[
        Paragraph("<b>Test Name / Parameter</b>", cell_style),
        Paragraph("<b>Result</b>", cell_style),
        Paragraph("<b>Units</b>", cell_style),
        Paragraph("<b>Normal Reference Interval</b>", cell_style),
        Paragraph("<b>Status Flag</b>", cell_style)
    ]]

    for row in tests_data:
        test_name, val, unit, ref, flag = row
        is_abnormal = flag in ["HIGH", "LOW", "CRITICAL"]
        status_para = Paragraph(flag, cell_bold_flag if is_abnormal else cell_style)
        val_para = Paragraph(f"<b>{val}</b>" if is_abnormal else val, cell_bold_flag if is_abnormal else cell_style)

        table_data.append([
            Paragraph(test_name, cell_style),
            val_para,
            Paragraph(unit, cell_style),
            Paragraph(ref, cell_style),
            status_para
        ])

    results_table = Table(table_data, colWidths=[2.5*inch, 1.0*inch, 1.0*inch, 1.5*inch, 1.0*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#fafafa")]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(results_table)
    elements.append(Spacer(1, 15))

    # Notes & Clinical Comments
    elements.append(Paragraph("CLINICAL COMMENTS & INTERPRETATION", section_style))
    for note in notes:
        elements.append(Paragraph(f"• {note}", cell_style))
        elements.append(Spacer(1, 4))

    # Footer Signoff
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    footer_text = Paragraph(
        "<i>Electronically verified by Dr. Sarah Jenkins, MD (Consultant Clinical Pathologist). "
        "Medical Disclaimer: These diagnostic test results must be interpreted clinically by the treating medical doctor.</i>",
        sub_title_style
    )
    elements.append(footer_text)

    doc.build(elements)
    return str(pdf_path)


def generate_all_samples():
    # Report 1: Diabetic & Lipid Panel
    p1 = {
        "name": "Robert Miller",
        "id": "PT-2026-8819",
        "age": "54 Years",
        "gender": "Male",
        "doctor": "Dr. Michael Chen, MD",
        "date": "2026-09-15"
    }
    tests1 = [
        ("Fasting Blood Glucose (FBS)", "142", "mg/dL", "70 - 99", "HIGH"),
        ("Postprandial Blood Glucose (PPBS)", "210", "mg/dL", "< 140", "HIGH"),
        ("Glycated Hemoglobin (HbA1c)", "7.8", "%", "< 5.7", "HIGH"),
        ("Total Cholesterol", "245", "mg/dL", "< 200", "HIGH"),
        ("Triglycerides", "230", "mg/dL", "< 150", "HIGH"),
        ("HDL Cholesterol", "36", "mg/dL", "> 40", "LOW"),
        ("LDL Cholesterol", "163", "mg/dL", "< 100", "HIGH"),
        ("VLDL Cholesterol", "46", "mg/dL", "< 30", "HIGH"),
        ("Serum Creatinine", "1.1", "mg/dL", "0.7 - 1.3", "NORMAL"),
        ("Blood Urea Nitrogen (BUN)", "18", "mg/dL", "7 - 20", "NORMAL")
    ]
    notes1 = [
        "Elevated Fasting Glucose and HbA1c of 7.8% consistent with poorly controlled Diabetes Mellitus Type 2.",
        "Combined dyslipidemia noted with elevated Total Cholesterol (245 mg/dL), elevated Triglycerides, and elevated atherogenic LDL.",
        "Renal parameters (Creatinine 1.1 mg/dL, BUN 18 mg/dL) currently within preserved reference limits.",
        "Advised endocrinology consultation, dietary carbohydrate/fat restriction, and therapeutic lifestyle intervention."
    ]
    build_pdf_report("Sample_Diabetic_Lipid_Panel.pdf", "METROPATH DIAGNOSTICS & RESEARCH CENTER", p1, tests1, notes1)

    # Report 2: Anemia & Complete Blood Count (CBC)
    p2 = {
        "name": "Emily Watson",
        "id": "PT-2026-4432",
        "age": "28 Years",
        "gender": "Female",
        "doctor": "Dr. Anita Sharma, MD",
        "date": "2026-09-18"
    }
    tests2 = [
        ("Hemoglobin (Hb)", "9.2", "g/dL", "12.0 - 15.5", "LOW"),
        ("Red Blood Cell Count (RBC)", "3.4", "x10^6/uL", "3.9 - 5.2", "LOW"),
        ("Hematocrit (PCV)", "28.5", "%", "36.0 - 46.0", "LOW"),
        ("Mean Corpuscular Volume (MCV)", "71.4", "fL", "80.0 - 100.0", "LOW"),
        ("Mean Corpuscular Hemoglobin (MCH)", "23.5", "pg", "27.0 - 33.0", "LOW"),
        ("Mean Corpuscular Hemoglobin Conc. (MCHC)", "30.1", "g/dL", "32.0 - 36.0", "LOW"),
        ("Red Cell Distribution Width (RDW)", "17.2", "%", "11.5 - 14.5", "HIGH"),
        ("White Blood Cell Count (WBC / TLC)", "6400", "/cumm", "4000 - 11000", "NORMAL"),
        ("Platelet Count", "295", "x10^3/uL", "150 - 450", "NORMAL")
    ]
    notes2 = [
        "Moderate microcytic hypochromic anemia demonstrated by low Hemoglobin (9.2 g/dL), low MCV (71.4 fL), and low MCH.",
        "Elevated RDW (17.2%) suggests anisocytosis, characteristic of iron deficiency anemia.",
        "Total leukocyte and platelet counts are within normal physiological thresholds.",
        "Recommended follow-up: Serum Ferritin, Total Iron Binding Capacity (TIBC), and dietary iron evaluation."
    ]
    build_pdf_report("Sample_Anemia_CBC_Report.pdf", "APEX HEALTHCARE MOLECULAR LABS", p2, tests2, notes2)

    # Report 3: Comprehensive Normal Checkup
    p3 = {
        "name": "David Miller",
        "id": "PT-2026-1055",
        "age": "35 Years",
        "gender": "Male",
        "doctor": "Dr. Kevin Adams, MD",
        "date": "2026-09-22"
    }
    tests3 = [
        ("Hemoglobin (Hb)", "15.2", "g/dL", "13.0 - 17.0", "NORMAL"),
        ("White Blood Cell Count (WBC / TLC)", "7200", "/cumm", "4000 - 11000", "NORMAL"),
        ("Platelet Count", "260", "x10^3/uL", "150 - 450", "NORMAL"),
        ("Fasting Blood Glucose (FBS)", "88", "mg/dL", "70 - 99", "NORMAL"),
        ("Total Cholesterol", "172", "mg/dL", "< 200", "NORMAL"),
        ("HDL Cholesterol", "52", "mg/dL", "> 40", "NORMAL"),
        ("LDL Cholesterol", "94", "mg/dL", "< 100", "NORMAL"),
        ("Triglycerides", "118", "mg/dL", "< 150", "NORMAL"),
        ("Serum Creatinine", "0.9", "mg/dL", "0.7 - 1.3", "NORMAL"),
        ("Alanine Aminotransferase (ALT / SGPT)", "26", "U/L", "7 - 56", "NORMAL"),
        ("Thyroid Stimulating Hormone (TSH)", "1.85", "uIU/mL", "0.4 - 4.0", "NORMAL")
    ]
    notes3 = [
        "All routine hematological, metabolic, lipid, renal, liver, and thyroid parameters are well within standard reference intervals.",
        "No evidence of anemia, dyslipidemia, hyperglycemia, or organ impairment.",
        "Continue maintaining balanced nutrition, regular cardiovascular exercise, and routine annual health surveillance."
    ]
    build_pdf_report("Sample_Comprehensive_Normal_Checkup.pdf", "ZENITH PREVENTIVE HEALTH CLINIC", p3, tests3, notes3)

    print("Sample PDF reports generated successfully!")


if __name__ == "__main__":
    generate_all_samples()
