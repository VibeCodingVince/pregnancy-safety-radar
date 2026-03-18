"""
BumpRadar Agent System

Agents:
- OrchestratorAgent: Routes scan requests to appropriate handlers
- SafetyClassifierAgent: Core classification engine (DB + AI fallback)
- ProductScannerAgent: Barcode lookup via local DB + Open Food Facts
- OCRAgent: Image-to-text extraction via OpenAI Vision
- ResearchAgent: Auto-expands ingredient database
- QAAgent: Quality assurance and validation
"""
from app.agents.orchestrator import OrchestratorAgent
from app.agents.safety_classifier import SafetyClassifierAgent
from app.agents.product_scanner import ProductScannerAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.research_agent import ResearchAgent
from app.agents.qa_agent import QAAgent

__all__ = [
    "OrchestratorAgent",
    "SafetyClassifierAgent",
    "ProductScannerAgent",
    "OCRAgent",
    "ResearchAgent",
    "QAAgent",
]
