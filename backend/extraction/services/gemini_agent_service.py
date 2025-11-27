"""Gemini-based agentic RAG service for enhanced document extraction."""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import time

from django.conf import settings

from .base_service import BaseExtractionService, ExtractionServiceError

logger = logging.getLogger(__name__)


class GeminiAgentError(ExtractionServiceError):
    """Specific exception for Gemini agent errors."""
    pass


class GeminiAgentService(BaseExtractionService):
    """
    Agentic RAG service using Google Gemini LLM.

    Supports:
    - Mock mode for development (USE_MOCK_GEMINI=True)
    - Real Gemini API calls (USE_MOCK_GEMINI=False)
    - Token counting for cost tracking
    - German construction domain prompts
    """

    # Token estimation ratios (based on Gemini tokenizer)
    TOKENS_PER_CHAR_INPUT = 0.25   # Roughly 4 chars per token
    TOKENS_PER_CHAR_OUTPUT = 0.25

    # Mock responses for development testing
    MOCK_RESPONSES = {
        'extract': {
            'confidence': 0.92,
            'extracted_fields': {
                'vendor_name': 'Musterfirma GmbH',
                'invoice_number': 'RE-2024-001',
                'amount': Decimal('1250.50'),
                'currency': 'EUR',
                'date': '2024-11-15',
                'gaeb_position': '01.001',
                'material': 'Eiche behandelt',
                'notes': 'Mock extraction result',
            },
            'reasoning': 'Mock mode active - no actual LLM processing',
            'improvements': []
        },
        'verify': {
            'verified': True,
            'confidence_adjustment': 0.02,
            'feedback': 'Extracted data appears complete and accurate',
        },
        'enhance': {
            'enhanced_fields': {
                'material_category': 'Hartholz',
                'complexity_factor': 1.2,
                'estimated_hours': 4.5,
            },
            'additional_insights': ['Material type identified', 'Complexity estimated'],
            'suggestions': []
        }
    }

    def __init__(self, config: Dict[str, Any], timeout_seconds: int = 30):
        """Initialize Gemini agent service.

        Args:
            config: Configuration dictionary (uses Django settings)
            timeout_seconds: API call timeout

        Raises:
            GeminiAgentError: If initialization fails
        """
        super().__init__(config, timeout_seconds)
        self.client = None
        self.model_name = settings.GEMINI_MODEL
        self.use_mock = settings.USE_MOCK_GEMINI
        self.api_key = settings.GEMINI_API_KEY

        # Token counting cache
        self.prompt_tokens_cache = {}

        self._initialize()

    def _initialize(self):
        """Initialize Gemini client or mock mode."""
        if self.use_mock:
            logger.info("GeminiAgentService initialized in MOCK mode")
            return

        if not self.api_key:
            logger.warning(
                "GEMINI_API_KEY not set. Falling back to mock mode. "
                "Set USE_MOCK_GEMINI=True to suppress this warning."
            )
            self.use_mock = True
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            logger.info(f"GeminiAgentService initialized with {self.model_name}")
        except ImportError:
            logger.warning(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )
            self.use_mock = True
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}. Using mock mode.")
            self.use_mock = True

    def process(self, file_path: str) -> Dict[str, Any]:
        """
        Process document file (not used for agent - use extract_with_agent instead).

        This method exists for interface compatibility but the primary
        method for agentic processing is extract_with_agent().

        Args:
            file_path: Path to file

        Returns:
            Placeholder dictionary
        """
        return {
            'status': 'not_implemented',
            'message': 'Use extract_with_agent() for agentic processing'
        }

    def extract_with_agent(
        self,
        extracted_text: str,
        current_fields: Dict[str, Any],
        confidence_scores: Dict[str, float],
        document_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int, Decimal]:
        """
        Use Gemini agent to enhance/verify document extraction.

        Args:
            extracted_text: Full OCR text from document
            current_fields: Currently extracted structured fields
            confidence_scores: Confidence scores for each field
            document_context: Optional context (previous similar documents, patterns)

        Returns:
            Tuple of:
            - enhanced_result: Dict with improved fields and metadata
            - tokens_used: Estimated or actual token count
            - cost_usd: Estimated cost in USD

        Raises:
            GeminiAgentError: If API call fails
        """
        start_time = time.time()

        # Build system and user prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_extraction_prompt(
            extracted_text,
            current_fields,
            confidence_scores,
            document_context
        )

        # Estimate tokens before API call
        input_tokens = self._estimate_tokens(
            system_prompt + user_prompt
        )

        if self.use_mock:
            return self._handle_mock_extraction(
                current_fields,
                input_tokens,
                time.time() - start_time
            )

        try:
            # Call Gemini API
            response = self.client.generate_content(
                user_prompt,
                generation_config={
                    'temperature': 0.3,  # Low temperature for consistency
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 2000,
                }
            )

            # Parse response
            result = self._parse_gemini_response(response.text)

            # Count actual tokens from response
            output_tokens = self._estimate_tokens(response.text)
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            cost_usd = self._calculate_cost(input_tokens, output_tokens)

            # Add metadata
            result['metadata'] = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'model': self.model_name,
            }

            logger.info(
                f"Gemini extraction succeeded. "
                f"Tokens: {total_tokens}, Cost: ${cost_usd:.4f}"
            )

            return result, total_tokens, cost_usd

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            # Return fallback result with current fields
            return self._handle_api_failure(
                current_fields,
                str(e),
                input_tokens
            )

    def verify_extraction(
        self,
        extracted_fields: Dict[str, Any],
        extracted_text: str
    ) -> Tuple[Dict[str, Any], int, Decimal]:
        """
        Verify extracted fields against source text using Gemini.

        Args:
            extracted_fields: Fields to verify
            extracted_text: Source OCR text

        Returns:
            Tuple of (verification_result, tokens_used, cost_usd)
        """
        start_time = time.time()

        prompt = self._build_verification_prompt(extracted_fields, extracted_text)
        input_tokens = self._estimate_tokens(prompt)

        if self.use_mock:
            result = self.MOCK_RESPONSES['verify'].copy()
            result['original_confidence'] = 0.85
            cost_usd = self._calculate_cost(input_tokens, 100)
            return result, input_tokens, cost_usd

        try:
            response = self.client.generate_content(prompt)
            result = self._parse_gemini_response(response.text)

            output_tokens = self._estimate_tokens(response.text)
            cost_usd = self._calculate_cost(input_tokens, output_tokens)

            return result, input_tokens + output_tokens, cost_usd

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {
                'verified': False,
                'error': str(e),
                'fallback': True
            }, input_tokens, Decimal('0')

    # === Prompt Building Methods ===

    def _build_system_prompt(self) -> str:
        """Build system prompt for German construction document extraction."""
        return """Du bist ein Experte für deutsche Bau- und Handwerksdokumente.

Deine Aufgaben:
1. Extrahiere strukturierte Daten aus Dokumenten
2. Verifiziere die Richtigkeit der Extraktion
3. Berücksichtige deutsche Formate:
   - Zahlen: 1.234,56 (Punkt = Tausender, Komma = Dezimal)
   - Daten: DD.MM.YYYY
   - Währung: EUR
4. Erkenne Handwerks-Terminologie (Holzarten, Komplexität, Oberflächen)
5. Sei konservativ bei Unsicherheiten - kennzeichne als 'nicht sicher'

Antworte immer als valides JSON."""

    def _build_extraction_prompt(
        self,
        text: str,
        current_fields: Dict[str, Any],
        confidence_scores: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build extraction enhancement prompt."""
        return f"""Analysiere dieses Bau-Dokument und verbessere die Extraktion.

OCR-Text (Auszug):
{text[:2000]}

Aktuell extrahierte Felder:
{json.dumps(current_fields, indent=2, ensure_ascii=False)}

Konfidenz-Scores:
{json.dumps(confidence_scores, indent=2)}

Aufgaben:
1. Überprüfe die Extraktion auf Fehler
2. Verbessere unvollständige oder fehlerhafte Felder
3. Füge wichtige fehlende Informationen hinzu
4. Erkenne Holzarten und Komplexitätsfaktoren
5. Berechne Preise korrekt nach deutschem Format

Antworte mit diesem JSON-Format:
{{
  "confidence": 0.0,
  "extracted_fields": {{}},
  "improvements": [],
  "reasoning": ""
}}"""

    def _build_verification_prompt(
        self,
        fields: Dict[str, Any],
        text: str
    ) -> str:
        """Build verification prompt."""
        return f"""Verifiziere diese Extraktion gegen den Original-Text.

Extrahierte Felder:
{json.dumps(fields, indent=2, ensure_ascii=False)}

Original-Text (Auszug):
{text[:1000]}

Prüfe:
1. Sind alle Werte im Original-Text zu finden?
2. Wurden die deutschen Formate (1.234,56) korrekt geparst?
3. Gibt es Unstimmigkeiten?

Antworte mit JSON:
{{
  "verified": true/false,
  "confidence_adjustment": 0.0,
  "feedback": "",
  "issues": []
}}"""

    # === Token & Cost Estimation ===

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses simple character-based estimation.
        More accurate token counting would require the tokenizer library.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return max(int(len(text) * self.TOKENS_PER_CHAR_INPUT), 1)

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """
        Calculate API cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD as Decimal
        """
        pricing = settings.GEMINI_BUDGET_CONFIG['MODEL_PRICING'].get(
            self.model_name,
            settings.GEMINI_BUDGET_CONFIG['MODEL_PRICING']['gemini-1.5-flash']
        )

        input_cost = Decimal(str(input_tokens)) * Decimal(
            str(pricing['input_per_1m_tokens'] / 1_000_000)
        )
        output_cost = Decimal(str(output_tokens)) * Decimal(
            str(pricing['output_per_1m_tokens'] / 1_000_000)
        )

        return input_cost + output_cost

    # === Response Parsing ===

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from Gemini.

        Args:
            response_text: Raw response text

        Returns:
            Parsed dictionary

        Raises:
            GeminiAgentError: If parsing fails
        """
        try:
            # Extract JSON from response (may have extra text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise GeminiAgentError("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            raise GeminiAgentError(f"Invalid JSON response: {e}")

    # === Fallback & Mock Handling ===

    def _handle_mock_extraction(
        self,
        current_fields: Dict[str, Any],
        input_tokens: int,
        elapsed_seconds: float
    ) -> Tuple[Dict[str, Any], int, Decimal]:
        """Handle mock extraction for development."""
        result = self.MOCK_RESPONSES['extract'].copy()
        result['original_fields'] = current_fields

        output_tokens = len(json.dumps(result)) // 4
        cost_usd = self._calculate_cost(input_tokens, output_tokens)

        result['metadata'] = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'processing_time_ms': int(elapsed_seconds * 1000),
            'model': self.model_name,
            'mock_mode': True,
        }

        logger.debug("Mock extraction completed")
        return result, input_tokens + output_tokens, cost_usd

    def _handle_api_failure(
        self,
        current_fields: Dict[str, Any],
        error_message: str,
        input_tokens: int
    ) -> Tuple[Dict[str, Any], int, Decimal]:
        """Handle API failure with fallback result."""
        logger.warning(f"Using fallback result due to API failure: {error_message}")

        return {
            'confidence': 0.0,
            'extracted_fields': current_fields,
            'improvements': [],
            'reasoning': f'API call failed: {error_message}. Returning original extraction.',
            'fallback_mode': True,
            'error': error_message,
        }, input_tokens, Decimal('0')
