import os
import httpx
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from backend.app.ai.exceptions import GeminiAPIException, RateLimitException

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "MOCK_MODE")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = float(os.getenv("TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
        self.top_p = float(os.getenv("TOP_P", "0.95"))
        self.top_k = int(os.getenv("TOP_K", "40"))
        self.timeout = float(os.getenv("AI_TIMEOUT", "30.0"))
        self.enable_mock = os.getenv("ENABLE_MOCK_AI", "true").lower() == "true" or self.api_key == "MOCK_MODE"

    def _translate_to_lang(self, text: str, lang: str) -> str:
        if not lang or lang == "en":
            return text
        
        translations = {
            "es": {
                "### Summary": "### Summary (ES)",
                "### Reasoning": "### Reasoning (ES)",
                "### Confidence": "### Confidence (ES)",
                "### Data Sources": "### Data Sources (ES)",
                "### Recommended Actions": "### Recommended Actions (ES)",
                "### Alternative Actions": "### Alternative Actions (ES)",
                "### Potential Risks": "### Potential Risks (ES)",
                "### Workflow": "### Workflow (ES)",
                "Gate D is currently experiencing a 42% spike": "La puerta D está experimentando actualmente un aumento del 42%",
                "Metro shuttle service is delayed": "El servicio de transporte del metro se retrasa",
                "Elevator 2 near Gate C is temporarily out of service": "El ascensor 2 cerca de la puerta C está temporalmente fuera de servicio",
                "Volunteer staffing analysis shows a shortage": "El análisis de personal voluntario muestra una escasez",
                "There are currently 3 active incidents": "Actualmente hay 3 incidentes activos",
                "Stadium operations status is Green": "El estado de las operaciones del estadio es Verde"
            },
            "fr": {
                "### Summary": "### Summary (FR)",
                "### Reasoning": "### Reasoning (FR)",
                "### Confidence": "### Confidence (FR)",
                "### Data Sources": "### Data Sources (FR)",
                "### Recommended Actions": "### Recommended Actions (FR)",
                "### Alternative Actions": "### Alternative Actions (FR)",
                "### Potential Risks": "### Potential Risks (FR)",
                "### Workflow": "### Workflow (FR)",
                "Gate D is currently experiencing a 42% spike": "La porte D connaît actuellement un pic de 42%",
                "Metro shuttle service is delayed": "Le service de navette du métro est retardé",
                "Elevator 2 near Gate C is temporarily out of service": "L'ascenseur 2 près de la porte C est temporairement hors service",
                "Volunteer staffing analysis shows a shortage": "L'analyse des effectifs bénévoles montre une pénurie",
                "There are currently 3 active incidents": "Il y a actuellement 3 incidents actifs",
                "Stadium operations status is Green": "Le statut des opérations du stade est Vert"
            },
            "pt": {
                "### Summary": "### Summary (PT)",
                "### Reasoning": "### Reasoning (PT)",
                "### Confidence": "### Confidence (PT)",
                "### Data Sources": "### Data Sources (PT)",
                "### Recommended Actions": "### Recommended Actions (PT)",
                "### Alternative Actions": "### Alternative Actions (PT)",
                "### Potential Risks": "### Potential Risks (PT)",
                "### Workflow": "### Workflow (PT)",
                "Gate D is currently experiencing a 42% spike": "O portão D está atualmente experimentando um pico de 42%",
                "Metro shuttle service is delayed": "O serviço de traslado do metrô está atrasado",
                "Elevator 2 near Gate C is temporarily out of service": "O elevador 2 perto do portão C está temporariamente fora de serviço",
                "Volunteer staffing analysis shows a shortage": "A análise de pessoal voluntário mostra uma escassez",
                "There are currently 3 active incidents": "Existem atualmente 3 incidentes ativos",
                "Stadium operations status is Green": "O status das operações do estádio é Verde"
            },
            "ar": {
                "### Summary": "### Summary (AR)",
                "### Reasoning": "### Reasoning (AR)",
                "### Confidence": "### Confidence (AR)",
                "### Data Sources": "### Data Sources (AR)",
                "### Recommended Actions": "### Recommended Actions (AR)",
                "### Alternative Actions": "### Alternative Actions (AR)",
                "### Potential Risks": "### Potential Risks (AR)",
                "### Workflow": "### Workflow (AR)",
                "Gate D is currently experiencing a 42% spike": "شهدت البوابة د حاليًا ارتفاعًا بنسبة 42٪",
                "Metro shuttle service is delayed": "تأخرت خدمة حافلات المترو",
                "Elevator 2 near Gate C is temporarily out of service": "المصعد 2 بالقرب من البوابة ج معطل مؤقتًا",
                "Volunteer staffing analysis shows a shortage": "تحليل موظفي المتطوعين يظهر نقصًا",
                "There are currently 3 active incidents": "هناك حاليا 3 حوادث نشطة",
                "Stadium operations status is Green": "حالة عمليات الاستاد خضراء"
            }
        }

        lang_trans = translations.get(lang.lower(), {})
        translated_text = text
        for en_str, trans_str in lang_trans.items():
            translated_text = translated_text.replace(en_str, trans_str)
            
        return translated_text

    def _get_mock_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        
        # Detect target language
        lang = "en"
        if "spanish" in prompt_lower or "español" in prompt_lower or "es" == prompt_lower:
            lang = "es"
        elif "french" in prompt_lower or "français" in prompt_lower or "fr" == prompt_lower:
            lang = "fr"
        elif "portuguese" in prompt_lower or "português" in prompt_lower or "pt" == prompt_lower:
            lang = "pt"
        elif "arabic" in prompt_lower or "العربية" in prompt_lower or "ar" == prompt_lower:
            lang = "ar"

        if "simulate" in prompt_lower or "surge" in prompt_lower or "emergency" in prompt_lower or "timeline" in prompt_lower:
            resp = (
                "### Summary\n"
                "Simulation scenario initiated. Predicting 95% probability of a 30-minute crowd congestion wave at Gate D during kickoff egress.\n\n"
                "### Reasoning\n"
                "Simulated arrivals volume (82,000 guests) vs turnstile ticket validation speed (60 tickets/min per gate) creates queue growth of 420 people/min.\n\n"
                "### Confidence\n"
                "0.97\n\n"
                "### Data Sources\n"
                "Simulated Ingress Telemetry Model, Historical FIFA Egress logs.\n\n"
                "### Recommended Actions\n"
                "Deploy 6 volunteers immediately to assist queue management; open secondary egress gates A & B.\n"
                "Execute command: Open Gate D\n\n"
                "### Alternative Actions\n"
                "Hold metro departures for 10 minutes to stagger station entry; bypass security checks for low-risk VIP zones.\n\n"
                "### Potential Risks\n"
                "Overcrowding near shuttle pick-up route B; elevator queue bottleneck at Gate C.\n\n"
                "### Workflow\n"
                "1. Open Gate D: Open Gate D to relieve predicted kickoff density. expected improvement: reduce congestion by 22%.\n"
                "2. Dispatch Volunteers: Dispatch Team Bravo (6 volunteers) to South Stand egress. expected improvement: coordinate line flow.\n"
                "3. Notify Security: Alert Gate D security team to backup queues."
            )
        elif "sustainability" in prompt_lower or "energy" in prompt_lower or "lighting" in prompt_lower or "carbon" in prompt_lower:
            resp = (
                "### Summary\n"
                "Sustainability Intelligence Plan: Recommended 15% drop in lighting brightness during match halftime and HVAC setback to 23C in VIP suites.\n\n"
                "### Reasoning\n"
                "Halftime crowd migration to concession stands reduces heat load in suites by 35%. Smart HVAC setback maintains thermal comfort while optimizing grid loads.\n\n"
                "### Confidence\n"
                "0.92\n\n"
                "### Data Sources\n"
                "Suite Temperature Sensors, Halftime Concession Telemetry, Grid Power Meters.\n\n"
                "### Recommended Actions\n"
                "Approve Halftime Energy setbacks; redirect waste volunteers to Zone 3 collection points.\n"
                "Execute command: Dispatch Volunteers\n\n"
                "### Alternative Actions\n"
                "Disable auxiliary screen backlights in non-public corridors; shut off escalator standby motors.\n\n"
                "### Potential Risks\n"
                "Halftime suit temp rises above 24C if sensor feedback fails; minor waste pile-up at East gate exit corridors.\n\n"
                "### Workflow\n"
                "1. Dispatch Volunteers: Dispatch Waste Management Team to concession bins. expected improvement: reduce littering by 30%."
            )
        elif "announcement" in prompt_lower or "broadcast" in prompt_lower or "public" in prompt_lower:
            resp = (
                "### Summary\n"
                "Multilingual Public Announcement Templates Generated:\n"
                "English: Attention guests, please redirect to Gate E to avoid Gate D queues.\n"
                "Spanish: Atención visitantes, por favor diríjanse a la Puerta E para evitar colas en la Puerta D.\n"
                "French: Attention invités, veuillez vous diriger vers la Porte E pour éviter les files d'attente de la Porte D.\n"
                "Portuguese: Atenção visitantes, por favor dirijam-se ao Portão E para evitar filas no Portão D.\n"
                "Arabic: انتباه أيها الضيوف، يرجى التوجه إلى البوابة E لتجنب طوابير البوابة D.\n\n"
                "### Reasoning\n"
                "Dynamic queue diversion announcements mitigate crowd density increases at turnstile zones.\n\n"
                "### Confidence\n"
                "0.99\n\n"
                "### Data Sources\n"
                "Dynamic Diversion Public Announcement Schema.\n\n"
                "### Recommended Actions\n"
                "Broadcast announcement templates over guest speaker systems.\n\n"
                "### Alternative Actions\n"
                "Display announcement text on main stadium giant screens.\n\n"
                "### Potential Risks\n"
                "Guest confusion if text is broadcast during live kickoff play."
            )
        elif "gate a" in prompt_lower or "gate d" in prompt_lower or "crowd" in prompt_lower or "congestion" in prompt_lower:
            resp = (
                "### Summary\n"
                "Gate D is currently experiencing a 42% spike in crowd density, causing bottleneck queues up to 15 minutes.\n\n"
                "### Reasoning\n"
                "Real-time CCTV telemetry feeds and ticketing systems indicate a surge of late arrivals combined with a slow ticket scanner at turnstile 4.\n\n"
                "### Confidence\n"
                "0.94\n\n"
                "### Data Sources\n"
                "Gate D Turnstile Log API, Zone 2 CCTV feeds, and Ticket Counter database.\n\n"
                "### Recommended Actions\n"
                "Open Gate D secondary gates immediately to relieve pressure; dispatch 3 extra stewards to assist visitors.\n"
                "Execute command: Open Gate D\n\n"
                "### Alternative Actions\n"
                "Redirect arriving crowds to Gate E using digital signage; hold entry scanning for 5 minutes to restore order.\n\n"
                "### Potential Risks\n"
                "Minor stampede risk at Gate D if queue time exceeds 25 minutes; crowd spillover to outer ring road.\n\n"
                "### Workflow\n"
                "1. Open Gate D: Crowd density predicted to exceed 92%. expected improvement: reduce congestion by 18%.\n"
                "2. Dispatch Volunteers: South Stand shifts are under-allocated by 5 volunteers."
            )
        elif "incident" in prompt_lower or "leak" in prompt_lower or "scanner failure" in prompt_lower or "what happened" in prompt_lower or "summary" in prompt_lower:
            resp = (
                "### Summary\n"
                "There are currently 3 active incidents in the stadium: a water leak in Zone 3, a minor medical issue at Gate B, and a ticket scanner failure at Gate D.\n\n"
                "### Reasoning\n"
                "Sensors and steward mobile alerts dispatched telemetry updates. The water leak requires facilities coordination; Gate B medical has a paramedic on-site.\n\n"
                "### Confidence\n"
                "0.96\n\n"
                "### Data Sources\n"
                "Aegis Dispatch logs, Facilities dashboard, and Medical Dispatch DB.\n\n"
                "### Recommended Actions\n"
                "Deploy Steward Team Bravo to Zone 3 to assist facilities team; approve Gate D scanner override.\n"
                "Execute command: Dispatch Volunteers\n\n"
                "### Alternative Actions\n"
                "Close the affected restroom in Zone 3; redirect Gate B paramedics to remain standby.\n\n"
                "### Potential Risks\n"
                "Slipping hazard in Zone 3 corridor; minor crowd entry delays at Gate D.\n\n"
                "### Workflow\n"
                "1. Dispatch Volunteers: Dispatch 6 volunteers. expected improvement: assist paramedic team and guide visitors."
            )
        elif "volunteer" in prompt_lower or "shortage" in prompt_lower or "overloaded" in prompt_lower:
            resp = (
                "### Summary\n"
                "Volunteer staffing analysis shows a shortage of 5 volunteers at the South Stand (Zone 5) during the 16:00 shift change.\n\n"
                "### Reasoning\n"
                "Two volunteer check-ins failed to register, and the scheduled roster is under-allocated for the expected guest volume.\n\n"
                "### Confidence\n"
                "0.90\n\n"
                "### Data Sources\n"
                "Volunteer Check-In Database, South Stand Gate Log.\n\n"
                "### Recommended Actions\n"
                "Dispatch Volunteers from the North Stand pool to South Stand; trigger push alerts to standby stewards.\n"
                "Execute command: Dispatch Volunteers\n\n"
                "### Alternative Actions\n"
                "Extend shift length for 3 active North Stand volunteers; hire temporary event stewards.\n\n"
                "### Potential Risks\n"
                "Understaffed turnstiles at South Stand leading to bottlenecking; volunteer burnout.\n\n"
                "### Workflow\n"
                "1. Dispatch Volunteers: Dispatch 6 volunteers to Zone 5 South Stand."
            )
        elif "transit" in prompt_lower or "delay" in prompt_lower or "shuttle" in prompt_lower or "transport" in prompt_lower:
            resp = (
                "### Summary\n"
                "Metro shuttle service is delayed by approximately 8 minutes due to traffic congestion on Outer Ring Road.\n\n"
                "### Reasoning\n"
                "Telemetry checks indicate shuttle speeds dropped from 35 km/h to 12 km/h. Arrival frequencies are now every 14 minutes instead of 6.\n\n"
                "### Confidence\n"
                "0.92\n\n"
                "### Data Sources\n"
                "Shuttle Telemetry API, Ring Road Google Maps Traffic integration.\n\n"
                "### Recommended Actions\n"
                "Approve Delay Shuttle notice on digital boards; request express corridor bypass route.\n"
                "Execute command: Delay Shuttle\n\n"
                "### Alternative Actions\n"
                "Increase active shuttle count by dispatching standby bus 3; redirect passengers to walk through path C.\n\n"
                "### Potential Risks\n"
                "Delayed guest entry at pre-match kickoff; passenger overcrowding at Metro Station Hub.\n\n"
                "### Workflow\n"
                "1. Delay Shuttle: Delay Shuttle Metro Shuttle service by 10 minutes. expected improvement: passenger arrival scheduling alignment."
            )
        elif "accessibility" in prompt_lower or "elevator" in prompt_lower or "barrier" in prompt_lower or "risks" in prompt_lower:
            resp = (
                "### Summary\n"
                "Elevator 2 near Gate C is temporarily out of service due to a mechanical error.\n\n"
                "### Reasoning\n"
                "Telemetry sensors logged a door lock fault at 15:42. Maintenance team has been notified.\n\n"
                "### Confidence\n"
                "0.98\n\n"
                "### Data Sources\n"
                "Elevator Status Telemetry, Facilities Incident Log.\n\n"
                "### Recommended Actions\n"
                "Redirect wheelchair visitors to Elevator 1 via Ramp B path; update accessibility transit boards.\n\n"
                "### Alternative Actions\n"
                "Deploy standby stewards to manually operate the chair lift at Gate C.\n\n"
                "### Potential Risks\n"
                "Minor mobility congestion at Ramp B; elevator repair time exceeds match exit timeline.\n\n"
                "### Workflow\n"
                "1. Dispatch Volunteers: Dispatch 3 volunteers to guide wheelchair guests to Ramp B."
            )
        elif "briefing" in prompt_lower or "executive" in prompt_lower:
            resp = (
                "### Summary\n"
                "Stadium operations status is Green with minor warnings. Current occupancy is 82%, turnstile throughput is optimal, and no critical incidents are open.\n\n"
                "### Reasoning\n"
                "Operational KPIs, transit flows, and incident queues are aggregated across all sectors.\n\n"
                "### Confidence\n"
                "0.95\n\n"
                "### Data Sources\n"
                "Executive KPI dashboard, Transit status database, CrowdSnapshot tracker.\n\n"
                "### Recommended Actions\n"
                "No immediate emergency actions required; maintain patrollings.\n\n"
                "### Alternative Actions\n"
                "Adjust pre-exit security readiness routines.\n\n"
                "### Potential Risks\n"
                "Potential congestion peak during match egress at 18:30.\n\n"
                "### Workflow\n"
                "1. Notify Security: Standby for egress checks."
            )

        else:
            resp = (
                "### Summary\n"
                "I am ready to assist you. Ask me about crowd flows, incident logs, volunteers, transit status, or accessibility issues.\n\n"
                "### Reasoning\n"
                "Parsed incoming general query. No specific operational issues were matching.\n\n"
                "### Confidence\n"
                "0.95\n\n"
                "### Data Sources\n"
                "Stadium Operations Manual, Database schemas.\n\n"
                "### Recommended Actions\n"
                "Select one of the suggested prompt cards or type your query in the console.\n\n"
                "### Alternative Actions\n"
                "View the command center dashboard for quick overrides.\n\n"
                "### Potential Risks\n"
                "None.\n\n"
                "### Workflow\n"
                "1. Notify Security: patrols verify secondary exits."
            )

        return self._translate_to_lang(resp, lang)

    async def generate_content(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        """Call Gemini API to generate content with retry backoff."""
        if self.enable_mock:
            await asyncio.sleep(0.1) # Simulate network
            mock_text = self._get_mock_response(prompt)
            if json_mode:
                return json.dumps({
                    "summary": mock_text.split("### Summary\n")[1].split("\n\n###")[0] if "### Summary\n" in mock_text else mock_text,
                    "reasoning": mock_text.split("### Reasoning\n")[1].split("\n\n###")[0] if "### Reasoning\n" in mock_text else "",
                    "confidence": 0.95,
                    "sources": mock_text.split("### Data Sources\n")[1].split("\n\n###")[0] if "### Data Sources\n" in mock_text else "",
                    "recommended_actions": mock_text.split("### Recommended Actions\n")[1].split("\n\n###")[0] if "### Recommended Actions\n" in mock_text else "",
                    "alternative_actions": mock_text.split("### Alternative Actions\n")[1].split("\n\n###")[0] if "### Alternative Actions\n" in mock_text else "",
                    "potential_risks": mock_text.split("### Potential Risks\n")[1] if "### Potential Risks\n" in mock_text else ""
                })
            return mock_text

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = {"parts": [{"text": prompt}]}
        config = {
            "temperature": self.temperature,
            "maxOutputTokens": self.max_tokens,
            "topP": self.top_p,
            "topK": self.top_k,
        }
        if json_mode:
            config["responseMimeType"] = "application/json"

        payload = {
            "contents": [contents],
            "generationConfig": config
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        headers = {"Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(3):
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 429:
                        if attempt == 2:
                            raise RateLimitException("Gemini API Rate Limit Exceeded.")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if response.status_code != 200:
                        raise GeminiAPIException(f"Gemini API Error: {response.text}")
                    
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise GeminiAPIException("No generation candidates returned from Gemini.")
                    
                    text = candidates[0]["content"]["parts"][0]["text"]
                    return text
                except httpx.HTTPError as e:
                    if attempt == 2:
                        raise GeminiAPIException(f"HTTP connection failed: {str(e)}")
                    await asyncio.sleep(1.5 ** attempt)
            
            raise GeminiAPIException("Failed to generate content after retries.")

    async def generate_stream(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chunks from the Gemini API."""
        if self.enable_mock:
            mock_text = self._get_mock_response(prompt)
            for chunk in mock_text.split(" "):
                await asyncio.sleep(0.01)
                yield chunk + " "
            return

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?key={self.api_key}"
        contents = {"parts": [{"text": prompt}]}
        payload = {
            "contents": [contents],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "topP": self.top_p,
                "topK": self.top_k,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        headers = {"Content-Type": "application/json"}

        # Using HTTPX streaming
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    raise GeminiAPIException(f"Gemini API streaming error: status {response.status_code}")
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    # Parse JSON chunks (Gemini streaming sends an array of Candidates)
                    while True:
                        try:
                            # Try to extract the next valid JSON object/array element from the stream
                            # (Gemini returns a JSON array of responses, so it's surrounded by [ ... ])
                            # For simplicity, we can do substring scanning or simple parsing
                            # Since this is standard JSON stream, let's parse cleanly if we can.
                            # A simple approach for line-based SSE or JSON arrays:
                            pass
                        except Exception:
                            break
                        # For production streaming, we yield chunks of the stream
                        yield chunk
