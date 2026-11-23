import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { GreenHeader } from "@/components/GreenHeader";
import { Screen } from "@/components/Screen";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

const FAQS = [
  {
    id: "risk",
    question: "What does the crop risk percentage mean?",
    answer:
      "It estimates how favourable recent weather has been for crop disease at your nearest field grid point. It is not a soil test or a confirmed diagnosis.",
  },
  {
    id: "soil",
    question: "Where do soil values come from?",
    answer:
      "The app shows reference soil properties from the trained grid table nearest to your coordinates. For a lab-confirmed result, use the Soil Health Card scheme.",
  },
  {
    id: "freshness",
    question: "How fresh is the field data?",
    answer:
      "Live telemetry and the current risk are fetched when you open or pull to refresh the Home screen. Historical risk is reconstructed with the ML API and cached for 6 hours.",
  },
  {
    id: "offline",
    question: "What if the API is offline?",
    answer:
      "The app shows a clear error with a retry button. Cached farm settings and chat history stay on your device.",
  },
  {
    id: "chat",
    question: "Can I attach a photo?",
    answer:
      "Photo attachments are not wired yet. Describe the symptoms in the chat and the assistant will use the latest crop and weather context.",
  },
];

export default function HelpScreen() {
  const [expanded, setExpanded] = useState<string | null>(FAQS[0].id);

  return (
    <Screen edges={["left", "right", "bottom"]}>
      <GreenHeader showBack title="Help & Support" />

      <View style={styles.body}>
        <View style={styles.introCard}>
          <Ionicons name="help-circle-outline" size={24} color={colors.greenDeep} />
          <View style={styles.introCopy}>
            <Text style={styles.introTitle}>Frequently asked questions</Text>
            <Text style={styles.introText}>
              Quick answers about risk, soil data and connectivity.
            </Text>
          </View>
        </View>

        {FAQS.map((faq) => {
          const open = expanded === faq.id;
          return (
            <View key={faq.id} style={styles.faqCard}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={faq.question}
                onPress={() => setExpanded(open ? null : faq.id)}
                style={styles.faqHeader}
              >
                <Text style={styles.question}>{faq.question}</Text>
                <Ionicons
                  name={open ? "chevron-up" : "chevron-down"}
                  size={18}
                  color={colors.greenDeep}
                />
              </Pressable>
              {open ? <Text style={styles.answer}>{faq.answer}</Text> : null}
            </View>
          );
        })}

        <View style={styles.note}>
          <Ionicons name="leaf-outline" size={16} color={colors.greenDeep} />
          <Text style={styles.noteText}>
            For urgent crop disease decisions, contact your local agriculture
            officer or a qualified agronomist.
          </Text>
        </View>
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
  introCopy: {
    flex: 1,
  },
  introTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
  },
  introText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    marginTop: 2,
  },
  faqCard: {
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  faqHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  question: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
    flex: 1,
  },
  answer: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
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
