import { Ionicons } from "@expo/vector-icons";

export type NotificationTone = "risk" | "scheme" | "weather" | "tip";

export type AppNotification = {
  id: string;
  title: string;
  body: string;
  time: string;
  tone: NotificationTone;
  icon: keyof typeof Ionicons.glyphMap;
};

export const NOTIFICATIONS: AppNotification[] = [
  {
    id: "risk-1",
    title: "Moderate crop risk tomorrow",
    body: "Recent weather favours leaf disease in your area. Scout your field today.",
    time: "Today",
    tone: "risk",
    icon: "shield-half-outline",
  },
  {
    id: "weather-1",
    title: "Rain expected in the next 24 hours",
    body: "Consider delaying irrigation and checking field drainage.",
    time: "Today",
    tone: "weather",
    icon: "rainy-outline",
  },
  {
    id: "scheme-1",
    title: "Soil Health Card scheme",
    body: "A lab soil test can confirm pH and nutrient status for your farm.",
    time: "Yesterday",
    tone: "scheme",
    icon: "flask-outline",
  },
  {
    id: "tip-1",
    title: "Weekly farming tip",
    body: "Early morning scouting gives the clearest view of pest activity.",
    time: "2 days ago",
    tone: "tip",
    icon: "bulb-outline",
  },
];
