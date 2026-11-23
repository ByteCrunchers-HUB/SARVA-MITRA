import { Ionicons } from "@expo/vector-icons";
import { Image, StyleSheet, Text, View } from "react-native";

import { GreenHeader } from "@/components/GreenHeader";
import { Screen } from "@/components/Screen";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

const FEATURES = [
  { icon: "leaf-outline", title: "Crop risk signal", text: "Weather-based disease proxy from the trained ML model." },
  { icon: "analytics-outline", title: "Field analytics", text: "Recent moisture, rainfall and temperature trends." },
  { icon: "chatbubble-ellipses-outline", title: "AI assistant", text: "Grounded advisory answers from the RAG pipeline." },
  { icon: "business-outline", title: "Scheme finder", text: "Quick links to Government of India farmer schemes." },
] as const;

export default function AboutScreen() {
  return (
    <Screen edges={["left", "right", "bottom"]}>
      <GreenHeader showBack title="About Sarva Mitra" />

      <View style={styles.body}>
        <View style={styles.hero}>
          <Image
            source={require("../../assets/logo.jpg")}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.heroTitle}>Smart Farming. Better Tomorrow.</Text>
          <Text style={styles.version}>Mobile edition · v1.0</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Our mission</Text>
          <Text style={styles.paragraph}>
            Sarva Mitra brings live field telemetry, a machine-learning risk
            signal and an AI advisory assistant into one simple tool for
            farmers. It is designed for low-bandwidth, phone-first use.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>What you can do</Text>
          {FEATURES.map((feature) => (
            <View key={feature.title} style={styles.featureRow}>
              <View style={styles.iconWrap}>
                <Ionicons name={feature.icon} size={19} color={colors.greenDeep} />
              </View>
              <View style={styles.featureCopy}>
                <Text style={styles.featureTitle}>{feature.title}</Text>
                <Text style={styles.featureText}>{feature.text}</Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.note}>
          <Ionicons name="information-circle-outline" size={16} color={colors.greenDeep} />
          <Text style={styles.noteText}>
            Crop risk is a weather-based proxy, not a laboratory soil-health
            report. Confirm agronomic decisions with a local expert.
          </Text>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    padding: spacing.lg,
    gap: spacing.lg,
  },
  hero: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    alignItems: "center",
  },
  logo: {
    width: 220,
    height: 76,
  },
  heroTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
    textAlign: "center",
    marginTop: spacing.md,
  },
  version: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    marginTop: 4,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  sectionTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
    marginBottom: spacing.sm,
  },
  paragraph: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
  },
  featureRow: {
    flexDirection: "row",
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.greenSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  featureCopy: {
    flex: 1,
  },
  featureTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  featureText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    marginTop: 2,
  },
  note: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    backgroundColor: colors.greenPale,
    borderRadius: radii.md,
    padding: spacing.md,
  },
  noteText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    flex: 1,
  },
});
