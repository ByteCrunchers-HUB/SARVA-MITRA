export const colors = {
  greenDeep: "#0B5D1E",
  greenDeepEnd: "#064A17",
  green: "#4CAF50",
  greenBright: "#57B85A",
  greenSoft: "#E8F5E9",
  greenPale: "#F1F8EE",
  page: "#F7F5EE",
  card: "#FFFFFF",
  text: "#1A2B1F",
  textBody: "#3D4A3F",
  textMuted: "#6F7D72",
  border: "#E3E7DF",
  red: "#D32F2F",
  redDark: "#B71C1C",
  redSoft: "#FDECEA",
  amber: "#F5A623",
  amberDark: "#7A4300",
  amberSoft: "#FFF4E0",
  blue: "#1E88E5",
  blueSoft: "#E3F2FD",
  white: "#FFFFFF",
  white90: "rgba(255,255,255,0.90)",
  white70: "rgba(255,255,255,0.70)",
  black: "#000000",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
} as const;

export const radii = {
  sm: 10,
  md: 14,
  lg: 18,
  xl: 22,
  xxl: 26,
  pill: 999,
} as const;

export const shadows = {
  card: {
    shadowColor: colors.greenDeep,
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  fab: {
    shadowColor: colors.greenDeep,
    shadowOpacity: 0.28,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
    elevation: 8,
  },
} as const;
