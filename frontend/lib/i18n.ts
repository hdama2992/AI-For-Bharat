type Lang = "en" | "hi";

const strings: Record<string, Record<Lang, string>> = {
  appName: { en: "Asha-GPT", hi: "आशा-GPT" },
  tagline: { en: "Your trusted health & wealth companion", hi: "आपका विश्वसनीय स्वास्थ्य और आय सहायक" },
  mandi: { en: "Mandi Advisor", hi: "मंडी सलाहकार" },
  pest: { en: "Pest-Vision", hi: "कीट-दृष्टि" },
  health: { en: "Health Triage", hi: "स्वास्थ्य जांच" },
  mandiDesc: { en: "Compare prices across nearby Mandis", hi: "आस-पास की मंडियों में भाव तुलना करें" },
  pestDesc: { en: "Identify crop diseases from a photo", hi: "फोटो से फसल की बीमारी पहचानें" },
  healthDesc: { en: "Check symptoms, get instant guidance", hi: "लक्षण बताएं, तुरंत मार्गदर्शन पाएं" },
  checkPrices: { en: "Check Prices", hi: "भाव देखें" },
  analyzeCrop: { en: "Analyze Crop", hi: "फसल जांचें" },
  checkHealth: { en: "Check Symptoms", hi: "लक्षण जांचें" },
  household: { en: "Household", hi: "परिवार" },
  green: { en: "Manage at Home", hi: "घर पर देखभाल करें" },
  yellow: { en: "Visit PHC Today", hi: "आज PHC जाएं" },
  red: { en: "CALL 108 NOW", hi: "अभी 108 कॉल करें" },
  disclaimer: {
    en: "This is not a medical diagnosis. Please consult a doctor.",
    hi: "यह चिकित्सा निदान नहीं है। कृपया डॉक्टर से मिलें।",
  },
};

export function t(key: string, lang: Lang): string {
  return strings[key]?.[lang] ?? key;
}
