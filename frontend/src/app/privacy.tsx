import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { GreenHeader } from "@/components/GreenHeader";
import { Screen } from "@/components/Screen";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

const SECTIONS = [
  {
    id: "data",
    title: "Data on this device",
    body: "Farm settings and chat history are stored locally with AsyncStorage. You can clear them from Profile → Logout.",
  },
  {
    id: "network",
    title: "Data sent to the API",
    body: "When you request a dashboard, prediction or advisory, your farm coordinates, crop and selected location are sent to the configured Sarva Mitra API.",
  },
  {
    id: "keys",
    title: "Keys and accounts",
    body: "The mobile app has no login and does not ship backend API keys. MongoDB and LLM credentials stay on the server.",
  },
  {
    id: "photos",
    title: "Photos",
    body: "Photo attachments are disabled. The app does not capture, upload or store farm photos.",
  },
  {
    id: "third",
    title: "External links",
    body: "Government scheme links open in your browser. Their privacy practices are managed by the linked departments.",
  },
];

export default function PrivacyScreen() {
  return (
    <Screen edges={["left", "right", "bottom"]}>
      <GreenHeader showBack title="Privacy Policy" />

      <View style={styles.body}>
        <View style={styles.introCard}>
          <Ionicons name="shield-checkmark-outline" size={24} color={colors.greenDeep} />
          <Text style={styles.introText}>
            Sarva Mitra keeps farm data simple, local and transparent.
          </Text>
        </View>

        {SECTIONS.map((section) => (
          <View key={section.id} style={styles.card}>
            <View style={styles.heading}>
              <Ionicons name="checkmark-circle-outline" size={18} color={colors.green} />
              <Text style={styles.title}>{section.title}</Text>
            </View>
            <Text style={styles.bodyText}>{section.body}</Text>
          </View>
        ))}

        <Text style={styles.footer}>
          Last updated: November 2026 · English edition
        </Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    padding: spacing.lg,
    gap: spacing.md,
  },
  introCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    backgroundColor: colors.greenPale,
    borderRadius: radii.lg,
    padding: spacing.md,
  },
  introText: {
    color: colors.textBody,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 20,
    flex: 1,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  heading: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.body,
    lineHeight: 22,
  },
  bodyText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
  },
  footer: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 15,
    textAlign: "center",
    marginTop: spacing.sm,
  },
});
