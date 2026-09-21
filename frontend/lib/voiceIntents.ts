export type VoiceIntent =
  | "scan_crop"
  | "show_farms"
  | "weather"
  | "read_last_result"
  | "talk_officer"
  | "change_language_hi";

export interface VoiceIntentRule {
  intent: VoiceIntent;
  keywords: Record<"en" | "hi" | "mr", string[]>;
}

export const VOICE_INTENTS: VoiceIntentRule[] = [
  {
    intent: "scan_crop",
    keywords: {
      en: ["scan my crop", "scan crop", "take a scan", "check my crop"],
      hi: ["मेरी फसल स्कैन", "फसल स्कैन", "फसल की जांच", "फसल जांच"],
      mr: ["माझे पीक स्कॅन", "पीक स्कॅन", "पिकाची तपासणी", "पीक तपासा"],
    },
  },
  {
    intent: "show_farms",
    keywords: {
      en: ["show my farms", "my farms", "farm list", "show farms"],
      hi: ["मेरे खेत दिखाओ", "मेरे खेत", "खेतों की सूची"],
      mr: ["माझी शेतं दाखवा", "माझी शेते", "शेतांची यादी"],
    },
  },
  {
    intent: "weather",
    keywords: {
      en: ["what is the weather", "weather", "weather report", "rain forecast"],
      hi: ["मौसम कैसा है", "मौसम", "बारिश का अनुमान"],
      mr: ["हवामान कसे आहे", "हवामान", "पावसाचा अंदाज"],
    },
  },
  {
    intent: "read_last_result",
    keywords: {
      en: ["read my last result", "read result", "tell me the result", "read aloud"],
      hi: ["मेरा परिणाम पढ़ो", "परिणाम पढ़ो", "जोर से पढ़ो"],
      mr: ["माझा निकाल वाचा", "निकाल वाचा", "मोठ्याने वाचा"],
    },
  },
  {
    intent: "talk_officer",
    keywords: {
      en: ["talk to officer", "contact officer", "ask an officer", "speak to officer"],
      hi: ["अधिकारी से बात", "अधिकारी से संपर्क", "अधिकारी को पूछो"],
      mr: ["अधिकाऱ्यांशी बोला", "अधिकाऱ्यांशी संपर्क", "अधिकाऱ्यांना विचारा"],
    },
  },
  {
    intent: "change_language_hi",
    keywords: {
      en: ["change language to hindi", "switch to hindi", "hindi language"],
      hi: ["हिंदी भाषा", "हिंदी में बदलो", "हिंदी चुनो"],
      mr: ["हिंदी भाषा", "हिंदीमध्ये बदला", "हिंदी निवडा"],
    },
  },
];

export function matchVoiceIntent(transcript: string, locale: "en" | "hi" | "mr"): VoiceIntent | null {
  const normalized = transcript.trim().toLocaleLowerCase();
  if (!normalized) return null;
  for (const rule of VOICE_INTENTS) {
    if (rule.keywords[locale].some((keyword) => normalized.includes(keyword.toLocaleLowerCase()))) {
      return rule.intent;
    }
  }
  return null;
}
