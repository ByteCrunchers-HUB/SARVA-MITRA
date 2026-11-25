import { Ionicons } from "@expo/vector-icons";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { MarkdownView } from "@/components/MarkdownView";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

type AdvisoryCardProps = {
  text: string;
  onAskAssistant: () => void;
  onDownloadReport?: () => void;
  isDownloading?: boolean;
};

export function AdvisoryCard({
  text,
  onAskAssistant,
  onDownloadReport,
  isDownloading = false,
}: AdvisoryCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.heading}>
        <View style={styles.iconWrap}>
          <Ionicons name="bulb-outline" size={20} color={colors.amberDark} />
        </View>
        <Text style={styles.title}>Quick Advisory</Text>
      </View>
      <MarkdownView content={text} baseTextStyle={styles.text} />
      <View style={styles.actionRow}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Ask the AI assistant"
          onPress={onAskAssistant}
          style={({ pressed }) => [styles.link, pressed && styles.pressed]}
        >
          <Text style={styles.linkText}>Ask Assistant</Text>
          <Ionicons name="arrow-forward" size={14} color={colors.greenDeep} />
        </Pressable>

        {onDownloadReport ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Download advisory report"
            onPress={onDownloadReport}
            disabled={isDownloading}
            style={({ pressed }) => [styles.downloadBtn, pressed && styles.pressed]}
          >
            {isDownloading ? (
              <ActivityIndicator size="small" color={colors.greenDeep} />
            ) : (
              <Ionicons name="download-outline" size={14} color={colors.greenDeep} />
            )}
            <Text style={styles.downloadText}>
              {isDownloading ? "Downloading..." : "Download Report"}
            </Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.amberSoft,
    borderRadius: radii.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: "#F6DFB6",
  },
  heading: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  iconWrap: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.body,
    lineHeight: 22,
  },
  text: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  link: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  downloadBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: "#F0D39B",
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: radii.md,
  },
  downloadText: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: 12,
    lineHeight: 16,
  },
  pressed: {
    opacity: 0.7,
  },
  linkText: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
  },
});
