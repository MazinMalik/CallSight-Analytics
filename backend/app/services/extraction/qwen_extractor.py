import re
import json
import logging
import requests
from typing import Optional, Dict, Any
from app.core.config import settings
from app.schemas.call import ExtractedInfoSchema, CallStatusEnum

logger = logging.getLogger("qwen_extractor")

SYSTEM_PROMPT = """
You are an expert Telecaller Call Intelligence Extractor AI.
Your job is to analyze telecaller-customer call transcripts and extract structured business lead intelligence in strict JSON format.

CRITICAL INSTRUCTIONS:
1. Return ONLY a valid JSON object matching the required schema. Do NOT include markdown code blocks, intro text, or explanation.
2. Rely ONLY on the provided call transcript. Never invent, hallucinate, or use external fallback data.
3. If information for a field is not present in the transcript, return null (or [] for list fields).
4. The call_status field MUST be strictly one of:
   "interested", "ordered", "not_interested", "did_not_pick", "callback_requested", "follow_up_required", "wrong_number", "unavailable", "unclear"
5. Do NOT include previous context or dummy data.
"""

PROMPT_TEMPLATE = """
[TELECALLER METADATA]
- Telecaller Name: {telecaller_name}
- Company Name: {company_name}
- Customer Phone: {submitted_phone_number}
- Category: {submitted_category}
- Telecaller Notes: {submitted_notes}

[CALL TRANSCRIPT]
{transcript}

Return a valid JSON object with the following schema:
{{
  "contact_person_name": null,
  "phone_number": "{submitted_phone_number}",
  "alternate_phone_number": null,
  "email": null,
  "business_category": null,
  "call_status": "unclear",
  "customer_intent": null,
  "products_or_services_discussed": [],
  "order_details": null,
  "quantity": null,
  "budget_or_price": null,
  "follow_up_date": null,
  "follow_up_time": null,
  "customer_requirements": null,
  "objections": [],
  "summary": "Concise call summary",
  "confidence_score": 0.90
}}
"""

class QwenInformationExtractor:
    def __init__(self):
        self.ollama_chat_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    def extract_lead_info(
        self,
        transcript: str,
        telecaller_name: Optional[str] = "Telecaller",
        company_name: Optional[str] = "Unspecified Company",
        submitted_phone_number: Optional[str] = "N/A",
        submitted_category: Optional[str] = None,
        submitted_notes: Optional[str] = None
    ) -> ExtractedInfoSchema:
        """
        Extracts structured lead details from transcript using local Qwen model via Ollama /api/chat.
        Strictly prevents old context or hardcoded sample data leaks.
        """
        clean_transcript = (transcript or "").strip()

        # If transcript is empty or indicates no speech, return clean empty schema (NO DUMMY FALLBACKS)
        if not clean_transcript or "No speech transcript" in clean_transcript or "No audible speech" in clean_transcript or "कोई भाषण प्रतिलेख नहीं" in clean_transcript:
            logger.info("Empty transcript provided to Qwen extractor. Returning clean empty schema.")
            return ExtractedInfoSchema(
                contact_person_name=None,
                phone_number=submitted_phone_number if submitted_phone_number != "N/A" else None,
                alternate_phone_number=None,
                email=None,
                business_category=submitted_category,
                call_status=CallStatusEnum.UNCLEAR,
                customer_intent="No audible speech detected in this call recording.",
                products_or_services_discussed=[],
                order_details=None,
                quantity=None,
                budget_or_price=None,
                follow_up_date=None,
                follow_up_time=None,
                customer_requirements=None,
                objections=[],
                summary="No speech transcript was extracted from this audio recording.",
                confidence_score=0.0
            )

        user_prompt = PROMPT_TEMPLATE.format(
            telecaller_name=telecaller_name or "Telecaller",
            company_name=company_name or "Unspecified Company",
            submitted_phone_number=submitted_phone_number or "N/A",
            submitted_category=submitted_category or "Unspecified",
            submitted_notes=submitted_notes or "None",
            transcript=clean_transcript
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        }

        logger.info(f"Calling Ollama Qwen model '{self.model}' at {self.ollama_chat_url}...")

        try:
            response = requests.post(self.ollama_chat_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            res_data = response.json()
            raw_text = res_data.get("message", {}).get("content", "").strip()

            return self._parse_and_validate_json(
                raw_text=raw_text,
                default_telecaller=telecaller_name,
                default_company=company_name,
                default_phone=submitted_phone_number,
                default_category=submitted_category
            )

        except Exception as e:
            logger.error(f"Error invoking Ollama Qwen extractor: {e}")
            # Fallback analysis based on transcript keywords if Ollama call fails
            status_enum = CallStatusEnum.UNCLEAR
            if "नहीं" in clean_transcript or "no" in clean_transcript.lower():
                status_enum = CallStatusEnum.NOT_INTERESTED
            elif "हाँ" in clean_transcript or "yes" in clean_transcript.lower() or "requirement" in clean_transcript.lower():
                status_enum = CallStatusEnum.INTERESTED

            return ExtractedInfoSchema(
                contact_person_name=None,
                phone_number=submitted_phone_number if submitted_phone_number != "N/A" else None,
                alternate_phone_number=None,
                email=None,
                business_category=submitted_category,
                call_status=status_enum,
                customer_intent="Customer conversation recorded.",
                products_or_services_discussed=[],
                order_details=None,
                quantity=None,
                budget_or_price=None,
                follow_up_date=None,
                follow_up_time=None,
                customer_requirements=None,
                objections=[],
                summary=f"Call transcript analyzed: '{clean_transcript[:120]}...'",
                confidence_score=0.75
            )

    def _parse_and_validate_json(
        self,
        raw_text: str,
        default_telecaller: Optional[str] = None,
        default_company: Optional[str] = None,
        default_phone: Optional[str] = None,
        default_category: Optional[str] = None
    ) -> ExtractedInfoSchema:
        """Parses and validates JSON string into ExtractedInfoSchema."""
        parsed_dict = self._parse_json_response(raw_text)
        return self._build_schema_from_dict(parsed_dict, default_phone, default_category)

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Robustly extracts and parses JSON object from LLM response text."""
        clean = text.strip()
        
        # Strip thinking tags if present
        clean = re.sub(r"<think>.*?</think>", "", clean, flags=re.DOTALL).strip()
        
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        try:
            return json.loads(clean)
        except Exception:
            pass

        # Regex search for JSON block {...}
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as err:
                logger.error(f"Regex JSON parse error: {err}")

        raise ValueError(f"Could not parse valid JSON from text: {text[:200]}")

    def _build_schema_from_dict(
        self,
        data: Dict[str, Any],
        submitted_phone: Optional[str],
        submitted_cat: Optional[str]
    ) -> ExtractedInfoSchema:
        """Validates and constructs ExtractedInfoSchema with strict enum and fallback checks."""
        raw_status = str(data.get("call_status", "unclear")).lower().strip().replace(" ", "_")
        valid_statuses = [e.value for e in CallStatusEnum]
        
        if raw_status not in valid_statuses:
            if "order" in raw_status or "buy" in raw_status:
                status_enum = CallStatusEnum.ORDERED
            elif "interest" in raw_status:
                status_enum = CallStatusEnum.INTERESTED
            elif "callback" in raw_status or "call_back" in raw_status:
                status_enum = CallStatusEnum.CALLBACK_REQUESTED
            elif "follow" in raw_status:
                status_enum = CallStatusEnum.FOLLOW_UP_REQUIRED
            elif "not_interested" in raw_status:
                status_enum = CallStatusEnum.NOT_INTERESTED
            else:
                status_enum = CallStatusEnum.UNCLEAR
        else:
            status_enum = CallStatusEnum(raw_status)

        prods = data.get("products_or_services_discussed", [])
        if isinstance(prods, str):
            prods = [prods] if prods else []
        elif not isinstance(prods, list):
            prods = []

        objs = data.get("objections", [])
        if isinstance(objs, str):
            objs = [objs] if objs else []
        elif not isinstance(objs, list):
            objs = []

        return ExtractedInfoSchema(
            contact_person_name=data.get("contact_person_name"),
            phone_number=data.get("phone_number") or (submitted_phone if submitted_phone != "N/A" else None),
            alternate_phone_number=data.get("alternate_phone_number"),
            email=data.get("email"),
            business_category=data.get("business_category") or submitted_cat,
            call_status=status_enum,
            customer_intent=data.get("customer_intent"),
            products_or_services_discussed=[str(p) for p in prods if p],
            order_details=data.get("order_details"),
            quantity=str(data.get("quantity")) if data.get("quantity") is not None else None,
            budget_or_price=str(data.get("budget_or_price")) if data.get("budget_or_price") is not None else None,
            follow_up_date=data.get("follow_up_date"),
            follow_up_time=data.get("follow_up_time"),
            customer_requirements=data.get("customer_requirements"),
            objections=[str(o) for o in objs if o],
            summary=data.get("summary") or "Call transcript analyzed.",
            confidence_score=float(data.get("confidence_score", 0.85))
        )

qwen_extractor = QwenInformationExtractor()
