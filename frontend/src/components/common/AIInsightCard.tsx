"use client";

import React, { useState, useEffect } from "react";
import { Brain, Sparkles, AlertTriangle, CheckCircle, ArrowRight, Globe, Shield, RefreshCw } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface AIInsightCardProps {
  page: "crowd" | "incident" | "transit" | "volunteer" | "accessibility" | "mission-control" | "command-center";
  extraData?: any;
  onExecuteCommand?: (command: string) => void;
}

const localInsights: Record<string, {
  summary: string;
  risk: string;
  prediction: string;
  recommendation: string;
  confidence: number;
  why: string;
  expectedImpact: string;
  suggestedCommand?: string;
  reasoningSteps: string[];
}> = {
  crowd: {
    summary: "Crowd flow bottleneck emerging at Gate D turnstiles. Ingress arrival rate (68 guests/min) exceeds validation rate (48 guests/min).",
    risk: "Medium",
    prediction: "Turnstile queues will expand to 15+ minutes delay within next 10 minutes if left unmanaged.",
    recommendation: "Open Gate D secondary bypass gates and redirect arriving guests to Gate E using digital signage.",
    confidence: 0.94,
    why: "Slow RFID validation checks detected on turnstiles 3 & 4 coupled with surge of late pre-match ticket scans.",
    expectedImpact: "Reduces Gate D queue density by 22% and clears turnstile backlog within 6 minutes.",
    suggestedCommand: "Open Gate D",
    reasoningSteps: [
      "Analyzing gate validation rates vs ticketing queue speed.",
      "Predicting congestion impact for Sector B and surrounding ring roads.",
      "Formulating gate override recommendation to balance load."
    ]
  },
  incident: {
    summary: "Water leak in Zone 3 corridor near restroom 3B causing a localized slipping hazard and pathway restriction.",
    risk: "Low",
    prediction: "High probability of guest slip injuries if pedestrian routing is not diverted around Corridor 3.",
    recommendation: "Deploy Maintenance Team to shut off valve 3B and dispatch 3 stewards to redirect crowd away from the corridor.",
    confidence: 0.96,
    why: "IoT water pressure drop registered on Zone 3 sub-meter, confirmed by steward mobile dispatch telemetry.",
    expectedImpact: "Neutralizes slipping hazard, redirects pedestrian traffic safely, and resolves leak within 12 minutes.",
    suggestedCommand: "Dispatch Volunteers",
    reasoningSteps: [
      "Detecting pressure drops in Zone 3 facilities pipeline.",
      "Correlating CCTV motion metrics with hazard area reports.",
      "Triggering emergency dispatch proposal for stewards."
    ]
  },
  transit: {
    summary: "Metro Shuttle Line experiencing an 8-minute headway delay due to temporary traffic build-up at Outer Ring Road junction.",
    risk: "Medium",
    prediction: "Transit delays could lead to a 10% late arrival spike for Gate A ticketing counters.",
    recommendation: "Deploy 2 standby buses to Metro Shuttle route and post dynamic delay announcements on transit boards.",
    confidence: 0.92,
    why: "GPS tracking on shuttle units 4 & 5 show average travel speed dropped to 12 km/h at the Ring Road junction.",
    expectedImpact: "Increases hourly passenger transit capacity by 200 people, stabilizing gate arrivals.",
    suggestedCommand: "Delay Shuttle",
    reasoningSteps: [
      "Checking headway telemetry for all active shuttle routes.",
      "Parsing external city traffic maps near Stadium outer rings.",
      "Generating standby fleet dispatch request."
    ]
  },
  volunteer: {
    summary: "Roster discrepancy detected: South Stand (Zone 5) is underallocated by 5 volunteer stewards during current shift transition.",
    risk: "Medium",
    prediction: "Zone 5 stands will face reduced supervision, causing minor entry bottlenecks at local stairs.",
    recommendation: "Dispatch Volunteer Team Bravo (5 stewards) from North Stand standby pool to South Stand.",
    confidence: 0.89,
    why: "Roster check-in data shows only 3 checked-in volunteers vs 8 scheduled, caused by local transport delays.",
    expectedImpact: "Restores required stewarding coverage and ensures continuous safe stairwell guidance in 8 minutes.",
    suggestedCommand: "Dispatch Volunteers",
    reasoningSteps: [
      "Scanning digital check-in logs for active shift volunteers.",
      "Identifying stand supervision gaps based on stand occupancy.",
      "Routing nearest standby volunteer team."
    ]
  },
  accessibility: {
    summary: "Elevator 2 near Gate C is temporarily out of service due to an automated mechanical door lock warning.",
    risk: "High",
    prediction: "Wheelchair guests at Gate C will face vertical mobility restrictions and extended ramp wait times.",
    recommendation: "Redirect wheelchair guests to Elevator 1 via Ramp B and deploy 2 stewards to assist manually at Elevator 2 lobby.",
    confidence: 0.98,
    why: "Elevator telemetry logged critical mechanical fault code E-204 at 15:42; tech team has been alerted.",
    expectedImpact: "Maintains ADA compliance and secures safe alternative paths for mobility-impaired guests.",
    suggestedCommand: "Dispatch Volunteers",
    reasoningSteps: [
      "Monitoring elevator IoT telemetry and fault diagnostic logs.",
      "Locating active wheelchair guests near Gate C zone.",
      "Mapping shortest accessible alternative route via Ramp B."
    ]
  },
  "mission-control": {
    summary: "Stadium health is optimal (94%) with moderate congestion risks at Gate D and transit shuttle routes.",
    risk: "Low",
    prediction: "Kickoff queue clearance predicted on-time. Egress plans are fully optimized.",
    recommendation: "Maintain standard matchday patrols, authorize pre-exit transit readiness codes, and monitor weather updates.",
    confidence: 0.95,
    why: "Aggregated telemetry shows ingress throughput is matching expectations with minor delays resolved by AI.",
    expectedImpact: "Maintains nominal stadium health score and safe operations leading to match kickoff.",
    suggestedCommand: "Open Gate D",
    reasoningSteps: [
      "Aggregating crowd, security, medical, and transit metrics.",
      "Calculating overall operational risk and resource margins.",
      "Publishing coordinated objectives for matchday operations."
    ]
  },
  "command-center": {
    summary: "High confidence operational commands prepared. AI recommends pre-emptive gate open overrides and shuttle delay alerts.",
    risk: "Low",
    prediction: "Manual command execution will stabilize turnstile ingress rates and transit flows.",
    recommendation: "Execute recommended commands for Gate D rate override and Shuttle dispatch.",
    confidence: 0.97,
    why: "Predictive modeling indicates early overrides prevent critical congestion peaks 15 minutes before match kickoff.",
    expectedImpact: "Stabilizes crowd flow and transit capacity prior to peak guest ingress window.",
    suggestedCommand: "Open Gate D",
    reasoningSteps: [
      "Validating playbook procedures against live telemetry.",
      "Running safety and conflict overrides for prepared commands.",
      "Securing command authorization metrics."
    ]
  }
};

const translations: Record<string, Record<string, string>> = {
  es: {
    "AI Live Reasoning": "Razonamiento en Vivo de IA",
    "Confidence": "Confianza",
    "Risk Score": "Puntuación de Riesgo",
    "Summary": "Resumen",
    "Prediction": "Predicción",
    "Why": "Por qué",
    "Recommendation": "Recomendación",
    "Expected Impact": "Impacto Esperado",
    "Live Analysis Steps": "Pasos de Análisis en Vivo",
    "Execute Recommended Command": "Ejecutar Comando Recomendado",
    "Translating...": "Traduciendo...",
    "Translate": "Traducir",
    "Generated": "Generado",
    "AI Insight Panel": "Panel de Información de IA",
    "Low": "Bajo",
    "Medium": "Medio",
    "High": "Alto",
    "Critical": "Crítico"
  },
  fr: {
    "AI Live Reasoning": "Raisonnement en Direct de l'IA",
    "Confidence": "Confiance",
    "Risk Score": "Score de Risque",
    "Summary": "Résumé",
    "Prediction": "Prédiction",
    "Why": "Pourquoi",
    "Recommendation": "Recommandation",
    "Expected Impact": "Impact Attendu",
    "Live Analysis Steps": "Étapes d'Analyse en Direct",
    "Execute Recommended Command": "Exécuter la Commande Recommandée",
    "Translating...": "Traduction...",
    "Translate": "Traduire",
    "Generated": "Généré",
    "AI Insight Panel": "Panneau d'Analyse IA",
    "Low": "Faible",
    "Medium": "Moyen",
    "High": "Élevé",
    "Critical": "Critique"
  },
  pt: {
    "AI Live Reasoning": "Raciocínio em Tempo Real da IA",
    "Confidence": "Confiança",
    "Risk Score": "Pontuação de Risco",
    "Summary": "Resumo",
    "Prediction": "Previsão",
    "Why": "Por que",
    "Recommendation": "Recomendação",
    "Expected Impact": "Impacto Esperado",
    "Live Analysis Steps": "Passos de Análise em Tempo Real",
    "Execute Recommended Command": "Executar Comando Recomendado",
    "Translating...": "Traduzindo...",
    "Translate": "Traduzir",
    "Generated": "Gerado",
    "AI Insight Panel": "Painel de Insights de IA",
    "Low": "Baixo",
    "Medium": "Médio",
    "High": "Alto",
    "Critical": "Crítico"
  },
  ar: {
    "AI Live Reasoning": "استدلال الذكاء الاصطناعي الحي",
    "Confidence": "الثقة",
    "Risk Score": "درجة الخطورة",
    "Summary": "الملخص",
    "Prediction": "التنبؤ",
    "Why": "السبب",
    "Recommendation": "التوصية",
    "Expected Impact": "التأثير المتوقع",
    "Live Analysis Steps": "خطوات التحليل الحي",
    "Execute Recommended Command": "تنفيذ الأمر الموصى به",
    "Translating...": "جاري الترجمة...",
    "Translate": "ترجم",
    "Generated": "تم التوليد",
    "AI Insight Panel": "لوحة رؤى الذكاء الاصطناعي",
    "Low": "منخفض",
    "Medium": "متوسط",
    "High": "مرتفع",
    "Critical": "حرج"
  }
};

export default function AIInsightCard({ page, extraData, onExecuteCommand }: AIInsightCardProps) {
  const [lang, setLang] = useState<string>("en");
  const [loadingTranslation, setLoadingTranslation] = useState<boolean>(false);
  const [translatedData, setTranslatedData] = useState<any>(null);
  const [generatedTime, setGeneratedTime] = useState<string>("");

  const baseInsight = localInsights[page] || localInsights.crowd;

  useEffect(() => {
    setGeneratedTime(new Date().toLocaleTimeString());
    setTranslatedData(null);
  }, [page]);

  const translateText = async (text: string, targetLang: string): Promise<string> => {
    if (targetLang === "en") return text;
    try {
      const res = await apiClient.post("/ai/translate", {
        text: text,
        target_language: targetLang
      });
      return res.data.translated_text || text;
    } catch (err) {
      console.warn("AI translation endpoint failed, falling back to mock dictionary/raw text.", err);
      const dict = translations[targetLang];
      if (dict && dict[text]) return dict[text];
      return `${text} (${targetLang.toUpperCase()})`;
    }
  };

  const handleLangChange = async (targetLang: string) => {
    setLang(targetLang);
    if (targetLang === "en") {
      setTranslatedData(null);
      return;
    }

    setLoadingTranslation(true);
    try {
      const transSummary = await translateText(baseInsight.summary, targetLang);
      const transRisk = await translateText(baseInsight.risk, targetLang);
      const transPred = await translateText(baseInsight.prediction, targetLang);
      const transRec = await translateText(baseInsight.recommendation, targetLang);
      const transWhy = await translateText(baseInsight.why, targetLang);
      const transImpact = await translateText(baseInsight.expectedImpact, targetLang);
      
      const transSteps = await Promise.all(
        baseInsight.reasoningSteps.map((step) => translateText(step, targetLang))
      );

      setTranslatedData({
        summary: transSummary,
        risk: transRisk,
        prediction: transPred,
        recommendation: transRec,
        why: transWhy,
        expectedImpact: transImpact,
        reasoningSteps: transSteps
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingTranslation(false);
    }
  };

  const display = translatedData || baseInsight;
  const t = (key: string) => {
    if (lang === "en") return key;
    return translations[lang]?.[key] || key;
  };

  const getRiskColor = (riskStr: string) => {
    const r = riskStr.toLowerCase();
    if (r.includes("critical") || r.includes("crítico") || r.includes("critique") || r.includes("حرج")) {
      return "bg-red-500/10 text-red-500 border-red-500/20";
    }
    if (r.includes("high") || r.includes("alto") || r.includes("élevé") || r.includes("مرتفع")) {
      return "bg-orange-500/10 text-orange-500 border-orange-500/20";
    }
    if (r.includes("medium") || r.includes("medio") || r.includes("moyen") || r.includes("متوسط")) {
      return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
    }
    return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
  };

  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-card to-background border border-primary/20 rounded-xl p-5 shadow-lg space-y-4 backdrop-blur-md">
      <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-primary/10 rounded-full blur-xl pointer-events-none animate-pulse"></div>

      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
            <Brain size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-1.5">
              {t("AI Insight Panel")}
              <Sparkles size={12} className="text-yellow-500" />
            </h3>
            <span className="text-[9px] text-muted-foreground block font-mono">
              {t("Generated")}: {generatedTime} | Model: gemini-2.5-flash
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-muted px-2 py-1 rounded text-[10px] font-semibold border border-border">
            <Globe size={11} className="text-muted-foreground" />
            <select
              value={lang}
              onChange={(e) => handleLangChange(e.target.value)}
              className="bg-transparent border-none outline-none cursor-pointer text-muted-foreground hover:text-foreground"
            >
              <option value="en">EN</option>
              <option value="es">ES</option>
              <option value="fr">FR</option>
              <option value="pt">PT</option>
              <option value="ar">AR</option>
            </select>
          </div>

          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider border ${getRiskColor(baseInsight.risk)}`}>
            {t("Risk Score")}: {display.risk}
          </span>
        </div>
      </div>

      {loadingTranslation ? (
        <div className="flex flex-col items-center justify-center py-6 gap-2">
          <RefreshCw size={24} className="text-primary animate-spin" />
          <span className="text-[10px] text-muted-foreground font-mono">{t("Translating...")}</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="bg-background/40 border border-border/40 rounded-lg p-3">
              <span className="text-[10px] text-primary/80 font-bold uppercase tracking-wider block mb-1">
                {t("Summary")}
              </span>
              <p className="text-xs font-medium text-foreground leading-relaxed">
                {display.summary}
              </p>
            </div>

            <div className="bg-background/40 border border-border/40 rounded-lg p-3">
              <span className="text-[10px] text-yellow-500 font-bold uppercase tracking-wider block mb-1">
                {t("Prediction")}
              </span>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {display.prediction}
              </p>
            </div>

            <div className="bg-background/40 border border-border/40 rounded-lg p-3">
              <span className="text-[10px] text-primary/80 font-bold uppercase tracking-wider block mb-1">
                {t("Why")}
              </span>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {display.why}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="bg-background/40 border border-primary/20 rounded-lg p-3 relative overflow-hidden">
              <span className="text-[10px] text-emerald-500 font-bold uppercase tracking-wider block mb-1 flex items-center gap-1">
                <CheckCircle size={10} />
                {t("Recommendation")}
              </span>
              <p className="text-xs font-semibold text-foreground leading-relaxed">
                {display.recommendation}
              </p>

              {baseInsight.suggestedCommand && (
                <button
                  onClick={() => onExecuteCommand?.(baseInsight.suggestedCommand!)}
                  className="mt-3 flex items-center gap-1 px-3 py-1.5 bg-primary text-primary-foreground font-bold text-[10px] rounded hover:bg-primary/95 transition-all shadow-sm"
                >
                  <span>{t("Execute Recommended Command")}</span>
                  <ArrowRight size={10} />
                </button>
              )}
            </div>

            <div className="bg-background/40 border border-border/40 rounded-lg p-3">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block mb-1">
                {t("Expected Impact")}
              </span>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {display.expectedImpact}
              </p>
            </div>

            <div className="bg-background/40 border border-border/40 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                  {t("Confidence")}
                </span>
                <span className="font-mono text-xs font-bold text-primary">
                  {Math.round(baseInsight.confidence * 100)}%
                </span>
              </div>
              <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden border border-border/30">
                <div
                  className="h-full bg-primary transition-all duration-500"
                  style={{ width: `${baseInsight.confidence * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!loadingTranslation && (
        <div className="bg-muted/30 border border-border/40 rounded-lg p-3 space-y-2">
          <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider block">
            {t("Live Analysis Steps")}
          </span>
          <div className="space-y-1.5 pl-2 border-l border-primary/20">
            {display.reasoningSteps?.map((step: string, idx: number) => (
              <div key={idx} className="flex items-start gap-2 text-[10px] text-muted-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-primary mt-1"></span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
