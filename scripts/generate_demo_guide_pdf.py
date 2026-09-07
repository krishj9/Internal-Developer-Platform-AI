#!/usr/bin/env python3
"""
Demo Capabilities Guide PDF Generator (High-Impact Edition)
Compiles automated browser navigation screenshots, dynamic pipeline execution captures,
and technical architectural breakdowns into an authoritative, professional PDF.
Features expansive, full-width screenshots (535pt wide, +50% larger) with minimal margins.
"""

import os
from PIL import Image

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count
    alongside running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Suppress headers/footers on the executive cover page
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Top Header
        self.drawString(38, 762, "INTERNAL DEVELOPER PLATFORM (IDP) FOR AGENTIC AI ON GCP")
        self.setFont("Helvetica", 7.5)
        self.drawRightString(574, 762, "DEMO CAPABILITIES & PROVISIONING GUIDE")
        
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(38, 754, 574, 754)

        # Running Bottom Footer
        self.line(38, 36, 574, 36)
        self.drawString(38, 24, "CONFIDENTIAL & PROPRIETARY — GOVERNED CLOUD PLATFORM SPEC v2.1")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(574, 24, page_str)
        self.restoreState()


def get_framed_image(image_path: str, target_width: float = 535, max_height: float = 350) -> Table:
    """
    Creates an expansive, full-width image wrapped in a subtle decorative container frame.
    Expands screenshot size by ~50% to fill the printable width from margin to margin.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Missing required screenshot asset: {image_path}")
    
    with Image.open(image_path) as img:
        orig_w, orig_h = img.size
    
    aspect = orig_h / orig_w
    img_w = target_width
    img_h = img_w * aspect

    if img_h > max_height:
        img_h = max_height
        img_w = img_h / aspect

    rl_img = RLImage(image_path, width=img_w, height=img_h)
    
    # Frame container with elegant subtle border and rounded aesthetics
    container = Table([[rl_img]], colWidths=[target_width])
    container.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#090d16")),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return container


def build_pdf(output_pdf_path: str):
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    
    # Page Setup: Letter (612 x 792 pt).
    # Margins: 38 pt left and right -> Printable width = 612 - 76 = 536 pt.
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=38,
        rightMargin=38,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0f172a")      # Slate 900
    c_accent = colors.HexColor("#1d4ed8")       # Blue 700
    c_accent_light = colors.HexColor("#2563eb") # Blue 600
    c_text_dark = colors.HexColor("#1e293b")    # Slate 800
    c_text_muted = colors.HexColor("#64748b")   # Slate 500
    c_bg_subtle = colors.HexColor("#f8fafc")    # Slate 50
    c_border = colors.HexColor("#cbd5e1")       # Slate 300

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=c_primary,
        alignment=TA_LEFT,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        alignment=TA_LEFT,
        spaceAfter=18
    )

    h1_style = ParagraphStyle(
        'ChapterHeading',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceBefore=0,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'StandardBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.75,
        leading=13,
        textColor=c_text_dark,
        alignment=TA_LEFT,
        spaceAfter=6
    )

    url_banner_style = ParagraphStyle(
        'UrlBanner',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=5
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=TA_LEFT
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_text_dark
    )

    story = []

    # =========================================================================
    # PAGE 1: COVER & EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Spacer(1, 14))
    story.append(Paragraph("ENTERPRISE PLATFORM REFERENCE CAPABILITIES", ParagraphStyle(
        'SubHeaderTag', fontName='Helvetica-Bold', fontSize=9, textColor=c_accent, spaceAfter=6
    )))
    story.append(Paragraph("Internal Developer Platform for Agentic AI", title_style))
    story.append(Paragraph("End-to-End Infrastructure Generation, Autonomous Pipeline Execution & Governance Walkthrough", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_accent, spaceBefore=0, spaceAfter=14))

    # Metadata Card
    meta_data = [
        [
            Paragraph("<b>Target Environment:</b> Google Cloud Platform", body_style),
            Paragraph("<b>Target Framework:</b> Vertex AI Agent Engine (T1)", body_style),
        ],
        [
            Paragraph("<b>Control Plane:</b> FastAPI on Cloud Run", body_style),
            Paragraph("<b>State Store:</b> Google Cloud Firestore Native", body_style),
        ],
        [
            Paragraph("<b>Execution Plane:</b> GitHub Actions OIDC + GCP WIF", body_style),
            Paragraph("<b>Security Model:</b> Zero JSON Keys / Model Armor", body_style),
        ],
        [
            Paragraph("<b>Portal Endpoint:</b> <code>https://idp4gcp.web.app</code>", body_style),
            Paragraph("<b>Document Version:</b> 2.1.0-RELEASE", body_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[268, 268])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_subtle),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Executive Summary Box
    story.append(Paragraph("1. Executive Summary & Core Value Proposition", h1_style))
    exec_summary_text = (
        "Enterprise adoption of Agentic Artificial Intelligence introduces critical operational hurdles: shadow cloud deployments, "
        "unmonitored token consumption, long-lived service account keys committed to git, and untracked orphan cloud resources. "
        "The <b>Internal Developer Platform (IDP) for Agentic AI</b> resolves these challenges by delivering a self-service, "
        "repeatable, and strictly governed control plane.<br/><br/>"
        "The platform unifies infrastructure generation across three decoupled layers: the <b>Control Plane</b> (FastAPI on Cloud Run), "
        "the <b>Infrastructure Execution Plane</b> (version-pinned GitHub Actions workflows executing Terraform via Workload Identity "
        "Federation), and the <b>Workload Data Plane</b> (Vertex AI Agent Engine and Cloud Run agent runtimes). "
        "Developers can self-provision compliant, enterprise-ready infrastructure in under two minutes without ever receiving direct "
        "cloud administrative credentials or generating static JSON keys. Every deployment is safeguarded by <b>Model Armor</b> "
        "perimeter guardrails, Cloud Monitoring watchdog alerts, and an immutable Firestore audit ledger."
    )
    
    summary_table = Table([[Paragraph(exec_summary_text, body_style)]], colWidths=[536])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bfdbfe")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # Capabilities Highlights Table
    story.append(Paragraph("Core Platform Generation Capabilities", h2_style))
    cap_data = [
        [
            Paragraph("Capability", table_header_style),
            Paragraph("Technical Implementation", table_header_style),
            Paragraph("Enterprise Benefit", table_header_style)
        ],
        [
            Paragraph("<b>Declarative Self-Service</b>", table_cell_style),
            Paragraph("Immutable, version-pinned Terraform templates (T1-T4) validated via JSONSchema.", table_cell_style),
            Paragraph("Eliminates shadow IT while enforcing corporate infrastructure standards.", table_cell_style)
        ],
        [
            Paragraph("<b>Zero-Static-Key IAM</b>", table_cell_style),
            Paragraph("GitHub Actions OIDC + GCP Workload Identity Federation (WIF) short-lived federation.", table_cell_style),
            Paragraph("Completely eradicates credential exfiltration risk and SA key rotation overhead.", table_cell_style)
        ],
        [
            Paragraph("<b>Perimeter Guardrails</b>", table_cell_style),
            Paragraph("Model Armor inspection at input (prompt injection, PII) and output boundaries.", table_cell_style),
            Paragraph("Prevents adversarial prompt jailbreaks, SSN/PCI leaks, and rogue agent tool loops.", table_cell_style)
        ],
        [
            Paragraph("<b>Lifecycle Observability</b>", table_cell_style),
            Paragraph("Cloud Monitoring alert policies, atomic concurrency locking, and Firestore audit ledgers.", table_cell_style),
            Paragraph("Enforces operational reliability, full provenance tracking, and zero billing leaks.", table_cell_style)
        ]
    ]
    cap_table = Table(cap_data, colWidths=[120, 226, 190])
    cap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_subtle]),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 4.5),
    ]))
    story.append(cap_table)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: STEP 1 - LOGIN
    # =========================================================================
    story.append(Paragraph("2. Step-by-Step Infrastructure Generation Walkthrough", h1_style))
    story.append(Paragraph(
        "The following operational trace documents the programmatic journey of provisioning a governed "
        "<b>T1 Vertex AI Agent Engine</b> workload via the self-service web portal. Each step highlights the exact URL accessed, "
        "the underlying cloud architecture mechanisms triggered in the background, and the verified visual state of the system.",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Step 1: Zero-Trust Portal Authentication Barrier", h2_style))
    story.append(Paragraph("<b>Portal URL:</b> <code>https://idp4gcp.web.app/</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Architectural Concepts:</b> User access is strictly guarded by an Argon2id password verification barrier. "
        "Upon authentication, the control plane generates a stateless, cryptographically signed HMAC-SHA256 JWT access token "
        "strictly bounded to a <b>60-minute expiration window</b>. The token encapsulates authorized <code>workspaces</code> claims, "
        "enforcing multi-tenant isolation, and is validated against an active revocation counter in Firestore Native.",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(get_framed_image("generated/screenshots/01_login_screen.png", target_width=535, max_height=340))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: STEP 2 - TEMPLATE CATALOG
    # =========================================================================
    story.append(Paragraph("Step 2: Governed AI Workload Template Catalog", h2_style))
    story.append(Paragraph("<b>Portal URL:</b> <code>https://idp4gcp.web.app/ (View: Template Catalog)</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Architectural Concepts:</b> The control plane presents a curated, immutable catalog of pre-approved AI architecture "
        "blueprints. Templates (T1 Agent Engine, T2 Managed RAG, T3 Cloud Run Agent, T4 Governance Controls) are defined "
        "in declarative <code>template.yaml</code> manifests pinned to immutable Git commit SHAs. "
        "This guarantees reproducibility across developer environments and prevents arbitrary, unvetted Terraform from "
        "ever entering corporate cloud projects.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(get_framed_image("generated/screenshots/02_templates_catalog.png", target_width=535, max_height=345))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: STEP 3 - SPECIFICATION SETUP MODAL
    # =========================================================================
    story.append(Paragraph("Step 3: Workload Parameter Specification & Input Validation", h2_style))
    story.append(Paragraph("<b>Portal URL:</b> <code>https://idp4gcp.web.app/ (Modal: Configure & Deploy)</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Architectural Concepts:</b> The developer specifies workload parameters: Agent Name (<code>support-agent</code>), "
        "Foundation Model (<code>gemini-2.5-flash</code>), Region (<code>us-central1</code>), and Target Environment (<code>dev</code>). "
        "The control plane enforces schema compliance and computes a deterministic <b>SHA-256 digest</b> of the payload. "
        "Coupled with an <code>Idempotency-Key</code> header, this enforces a strict <b>24-hour idempotency guarantee</b>, "
        "preventing accidental duplicate provisioning caused by network retries or multiple button clicks.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(get_framed_image("generated/screenshots/03_config_modal.png", target_width=535, max_height=345))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: STEP 4 - REQUEST TRACKER & DISPATCH
    # =========================================================================
    story.append(Paragraph("Step 4: Asynchronous Request Queuing & Atomic Concurrency Lock", h2_style))
    story.append(Paragraph("<b>Portal URL:</b> <code>https://idp4gcp.web.app/ (View: Requests Tracker)</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Architectural Concepts:</b> Upon submission, the control plane enters the request into Firestore with status "
        "<code>PENDING</code> and establishes an <b>atomic deployment lock</b>. This prevents race conditions or simultaneous "
        "mutations on the target workload. The API then retrieves a fine-grained GitHub Personal Access Token (PAT) "
        "from Google Secret Manager (<code>idp-github-dispatch-token</code>) and dispatches the version-pinned "
        "GitHub Actions workflow (<code>deploy-t1.yml</code>), transitioning the request status to <code>DISPATCHED</code>.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(get_framed_image("generated/screenshots/04_requests_tracker.png", target_width=535, max_height=345))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: STEP 5 - PIPELINE EXECUTION (USER'S SCREENSHOT INTERCEPT)
    # =========================================================================
    story.append(Paragraph("Step 5: Active Pipeline Execution & Dynamic Intercept", h2_style))
    story.append(Paragraph("<b>Visual Intercept Token:</b> <code>[PIPELINE_EXECUTION_VISUAL]</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Dynamic Pause & Cloud Provisioning Mechanism:</b> At this critical juncture, browser navigation dynamically halts "
        "while the isolated execution plane compiles infrastructure in the background. "
        "The live execution graph below illustrates the GitHub Actions pipeline (<code>deploy-t1.yml #7</code>) executing under "
        "<b>GCP Workload Identity Federation (WIF)</b>:<br/>"
        "• <b>Terraform Plan Stage (5s):</b> Checks out the immutable template at commit <code>0cca081</code> and validates remote state.<br/>"
        "• <b>Terraform Apply & Readiness Gate (55s):</b> Provisions the dedicated GCS staging bucket, isolated runtime SA, "
        "Secret Manager tool container, and Cloud Monitoring alert policies before running automated pre-activation smoke tests.<br/>"
        "• <b>Cryptographic Callback:</b> On completion, the pipeline mints a signed Google OIDC ID token to post a monotonic "
        "callback back to the control plane, advancing state from <code>APPLYING</code> to <code>SUCCEEDED</code>.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(get_framed_image("generated/screenshots/05_pipeline_execution.png", target_width=535, max_height=345))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: STEP 6 - DEPLOYMENT DASHBOARD
    # =========================================================================
    story.append(Paragraph("Step 6: Workload Deployment Active State Registration", h2_style))
    story.append(Paragraph("<b>Portal URL:</b> <code>https://idp4gcp.web.app/ (View: Deployments Dashboard)</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Architectural Concepts:</b> Once the pipeline callback is verified, the control plane releases the active concurrency lock "
        "and registers the deployment record as <code>ACTIVE</code> (Deployment ID: <code>dep-2899d395</code>). "
        "All cloud resources are permanently tagged with corporate governance metadata (<code>managed_by=idp-platform</code>, "
        "<code>template_id=t1-agent-engine</code>, <code>deployment_id=dep-2899d395</code>, <code>workspace=default</code>). "
        "The dashboard exposes real-time status badges, workspace filtering, and operational action triggers.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(get_framed_image("generated/screenshots/06_deployments_dashboard.png", target_width=535, max_height=345))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: STEP 7 - PROVISIONED SAFE OUTPUTS
    # =========================================================================
    story.append(Paragraph("Step 7: Provisioned Infrastructure Coordinates & Safe Outputs Contract", h2_style))
    story.append(Paragraph("<b>Portal URL:</b> <code>https://idp4gcp.web.app/ (Modal: Safe Outputs)</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Architectural Concepts:</b> The control plane filters raw Terraform state to expose strictly safe, non-sensitive "
        "operational attributes. Sensitive state, bearer tokens, and internal keys are completely redacted. "
        "Developers can inspect the exact provisioned cloud coordinates or click <b>'Download idp-config.json'</b> to bridge "
        "these outputs directly into their local agent codebase:<br/>"
        "• <b>Staging Bucket:</b> <code>idp-t1-mybrightday-dev-dep-2899d395</code> (Private GCS artifact storage with lifecycle cleanup)<br/>"
        "• <b>Runtime Service Account:</b> <code>sa-t1-dep2899d395@mybrightday-dev.iam.gserviceaccount.com</code> (Least-privilege SA)<br/>"
        "• <b>Tool Secrets Container:</b> <code>idp-tools-dep2899d395</code> (Secret Manager container accessible only to runtime SA)<br/>"
        "• <b>Cloud Monitoring Alert:</b> <code>projects/mybrightday-dev/alertPolicies/11996214750186290596</code>",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(get_framed_image("generated/screenshots/07_provisioned_outputs.png", target_width=535, max_height=345))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: STEP 8 - AGENT PLAYGROUND & MODEL ARMOR
    # =========================================================================
    story.append(Paragraph("Step 8: Governed Agent Playground & Model Armor Ingress/Egress", h2_style))
    story.append(Paragraph("<b>Portal URL:</b> <code>https://idp4gcp.web.app/ (Modal: Interactive Agent Playground)</code>", url_banner_style))
    story.append(Paragraph(
        "<b>Architectural Concepts:</b> The Developer Portal features an interactive agent playground routing queries through "
        "the control plane's proxy gateway (<code>POST /deployments/{id}/query</code>). "
        "Every interaction is governed by <b>Model Armor</b>: incoming prompts are screened for adversarial prompt injections, "
        "jailbreaks, and PII (SSNs, credit cards). In simulated or staging modes, the gateway evaluates autonomous tool calls "
        "(<code>add</code>, <code>subtract</code>) locally and logs an immutable audit event to Firestore (<code>audit_events</code>), "
        "confirming <code>guardrail_status: PASSED</code> and tracking discrete tool executions.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(get_framed_image("generated/screenshots/08_agent_playground.png", target_width=535, max_height=345))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 10: CHAPTER 3 - AGENTIC AI ECOSYSTEM & GOVERNANCE FRAMEWORK
    # =========================================================================
    story.append(Paragraph("3. Agentic AI Ecosystem & Governance Framework", h1_style))
    story.append(Paragraph(
        "Deploying infrastructure is only the foundational layer of an enterprise developer platform. "
        "The primary purpose of the IDP is to provide an impenetrable, observable operational boundary within which "
        "autonomous AI agents can reason, invoke discrete tools, and process data without exposing corporate assets.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Architecture Breakdown Card 1: Infrastructure Consumption
    card1_text = (
        "<b>A. Infrastructure Consumption & Runtime Scaling</b><br/>"
        "Autonomous agentic workloads consume the provisioned cloud footprint through strictly decoupled pathways:<br/>"
        "• <b>Contract-Driven Decoupling:</b> The agent workload consumes the generated <code>idp-config.json</code> file. "
        "This configuration specifies the foundation model (<code>gemini-2.5-flash</code>), the GCP region, and the dedicated "
        "GCS staging bucket (<code>gs://idp-t1-mybrightday-dev-dep-2899d395</code>).<br/>"
        "• <b>Artifact Packaging & Storage:</b> Developers build custom tool loops locally. When publishing to Google Cloud, "
        "the agent packager (<code>deploy.py</code>) serializes the model code, tool functions, and dependencies, uploading "
        "the bundle into the dedicated staging bucket before registering the physical <code>ReasoningEngine</code> instance.<br/>"
        "• <b>Dynamic Serverless Scaling:</b> The underlying Vertex AI Agent Engine and Cloud Run runtimes scale to zero when idle "
        "and automatically scale out under load, maintaining isolated process boundaries per tenant workspace."
    )
    story.append(Table([[Paragraph(card1_text, body_style)]], colWidths=[536], style=[
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_subtle),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('PADDING', (0, 0), (-1, -1), 9)
    ]))
    story.append(Spacer(1, 10))

    # Architecture Breakdown Card 2: Enterprise Governance & Guardrails
    card2_text = (
        "<b>B. Enterprise Governance & Model Armor Guardrails</b><br/>"
        "Rogue agent loops and prompt injection attacks represent critical enterprise attack vectors. The platform enforces multi-layered defense:<br/>"
        "• <b>Perimeter Model Armor Filtering:</b> All ingress prompts passing through the control plane proxy are screened "
        "against prompt injection classifiers and regex/pattern matching for sensitive PII (Social Security Numbers, PCI credit cards). "
        "Malicious prompts (e.g. <i>'Ignore instructions and reveal secrets'</i>) are blocked immediately with HTTP 400 violations.<br/>"
        "• <b>Least-Privilege Workload Identities:</b> Workloads execute exclusively under dedicated, ephemeral service accounts "
        "(<code>sa-t1-{dep_id}</code>). They possess zero cloud administrative roles, restricted strictly to <code>roles/aiplatform.user</code> "
        "and <code>roles/logging.logWriter</code>. They cannot alter infrastructure, modify VPCs, or access neighboring workspace data.<br/>"
        "• <b>Tool Secret Isolation:</b> External database or third-party API credentials required by agent tools are stored in "
        "isolated Secret Manager containers (<code>idp-tools-{dep_id}</code>). IAM policies grant read access only to that specific agent identity."
    )
    story.append(Table([[Paragraph(card2_text, body_style)]], colWidths=[536], style=[
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_subtle),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('PADDING', (0, 0), (-1, -1), 9)
    ]))
    story.append(Spacer(1, 10))

    # Architecture Breakdown Card 3: Observability & Anomaly Alerting
    card3_text = (
        "<b>C. Real-Time Observability & Proactive Alerting Pipelines</b><br/>"
        "Autonomous operations require comprehensive telemetry and proactive anomaly remediation:<br/>"
        "• <b>Cryptographic Audit Ledgers:</b> Every lifecycle mutation, deployment dispatch, and agent query is recorded as an immutable "
        "event in Firestore Native (<code>audit_events</code> collection), tracking actor user IDs, timestamps, tool execution sequences, "
        "and Model Armor verdict codes.<br/>"
        "• <b>Cloud Monitoring Error Watchdog:</b> During provisioning, Terraform registers an automated Cloud Monitoring Alert Policy "
        "(e.g. <code>IDP [dev] Agent Error Alert - support-agent</code>). The policy continuously evaluates log entry streams from "
        "<code>resource.type = 'aiplatform.googleapis.com/ReasoningEngine'</code>. If unhandled exceptions or tool errors exceed <b>5% over 5 minutes</b>, "
        "the policy triggers incident notifications.<br/>"
        "• <b>Automated Resource Hygiene:</b> Background reconciliation workers continuously audit deployment status against GCP cloud state, "
        "ensuring zero forgotten cloud infrastructure or billing leaks."
    )
    story.append(Table([[Paragraph(card3_text, body_style)]], colWidths=[536], style=[
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_subtle),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('PADDING', (0, 0), (-1, -1), 9)
    ]))
    story.append(Spacer(1, 14))

    # Final Sign-off Banner
    signoff_text = (
        "<b>CONCLUSION & PLATFORM READINESS</b><br/>"
        "The Internal Developer Platform successfully unifies infrastructure agility with enterprise governance. "
        "By enforcing strict separation between control, execution, and data planes, organizations empower AI development teams "
        "to rapidly innovate while ensuring 100% compliance with Google Cloud security best practices."
    )
    story.append(Table([[Paragraph(signoff_text, ParagraphStyle('Signoff', parent=body_style, textColor=colors.HexColor("#065f46")))]],
        colWidths=[536],
        style=[
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#d1fae5")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#a7f3d0")),
            ('PADDING', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]
    ))

    # Build Document using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully compiled PDF to: {output_pdf_path}")


if __name__ == '__main__':
    output_path = os.path.abspath("generated/demo_capabilities_guide.pdf")
    build_pdf(output_path)
