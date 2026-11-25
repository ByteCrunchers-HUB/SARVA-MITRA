import { Ionicons } from "@expo/vector-icons";

export type Scheme = {
  id: string;
  title: string;
  subtitle: string;
  url: string;
  icon: keyof typeof Ionicons.glyphMap;
};

export const SCHEMES: Scheme[] = [
  {
    id: "pm-kisan",
    title: "PM-KISAN",
    subtitle: "Direct income support for farmers",
    url: "https://pmkisan.gov.in/",
    icon: "cash-outline",
  },
  {
    id: "soil-health-card",
    title: "Soil Health Card Scheme",
    subtitle: "Get a soil health card & recommendations",
    url: "https://soilhealth.dac.gov.in/",
    icon: "flask-outline",
  },
  {
    id: "pmfby",
    title: "Pradhan Mantri Fasal Bima Yojana",
    subtitle: "Crop insurance for farmers",
    url: "https://pmfby.gov.in/",
    icon: "shield-checkmark-outline",
  },
  {
    id: "kcc",
    title: "Kisan Credit Card",
    subtitle: "Credit support for farm needs",
    url: "https://www.myscheme.gov.in/schemes/kcc",
    icon: "card-outline",
  },
  {
    id: "enam",
    title: "e-NAM",
    subtitle: "National agriculture market",
    url: "https://www.enam.gov.in/",
    icon: "storefront-outline",
  },
  {
    id: "pmksy",
    title: "PM Krishi Sinchayee Yojana",
    subtitle: "Irrigation support",
    url: "https://pmksy.gov.in/",
    icon: "water-outline",
  },
];
