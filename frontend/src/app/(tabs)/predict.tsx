import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { ApiErrorState } from "@/components/ApiErrorState";
import { GreenHeader } from "@/components/GreenHeader";
import { IconButton } from "@/components/IconButton";
import { PrimaryButton } from "@/components/PrimaryButton";
import { RiskGauge } from "@/components/RiskGauge";
import { Screen } from "@/components/Screen";
import { SoilReferenceCard } from "@/components/SoilReferenceCard";
import { soilReferenceForFarm } from "@/data/soilSnapshot";
import { useDashboard } from "@/hooks/useDashboard";
import { useFarmConfig } from "@/hooks/useFarmConfig";
import { downloadAdvisoryReport } from "@/utils/report";
import { colors, fonts, radii, sizes, spacing } from "@/theme";
import { formatRelativeTime, riskSoftColor } from "@/utils/format";

const ACTIONS: Record<string, string[]> = {
  low: [
    "Continue routine field scouting.",
    "Maintain the current irrigation schedule.",
    "Check the weather again tomorrow.",
  ],
  moderate: [
    "Scout leaves every 2 days for early spots.",
    "Avoid excess irrigation and dense canopy growth.",
    "Improve airflow around the crop where possible.",
  ],
  high: [
    "Inspect the field today for symptoms.",
    "Improve drainage and reduce leaf wetness.",
    "Consult a local agronomist before spraying.",
  ],
};

export default function PredictScreen() {
  const { farm } = useFarmConfig();
  const dashboard = useDashboard(farm);
  const soil = soilReferenceForFarm(farm);
  const risk = dashboard.data?.ml_risk;
  const level = risk?.risk_level ?? "low";
  const actions = ACTIONS[level] ?? ACTIONS.low;
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    if (isDownloading) return;
    setIsDownloading(true);
    try {
      await downloadAdvisoryReport({
        farm,
      });
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Screen edges={["left", "right"]}>
      <GreenHeader
        title="Crop Risk Prediction"
        subtitle={`${farm.crop} · ${farm.stage} · ${farm.location}`}
        right={
          <IconButton
            accessibilityLabel="Download Advisory Report"
            name={isDownloading ? "hourglass-outline" : "download-outline"}
            disabled={isDownloading}
            onPress={() => void handleDownload()}
          />
        }
      />

      <View style={styles.body}>
        <View
          style={[
            styles.gaugeCard,
            { backgroundColor: risk ? riskSoftColor(level) : colors.card },
          ]}
        >
          <Text style={styles.eyebrow}>TOMORROW’S CROP RISK</Text>
          <RiskGauge pct={risk?.risk_pct ?? null} level={level} />
          <Text style={styles.gaugeCaption}>
            Weather-based disease signal for your nearest field grid point.
          </Text>
          {dashboard.data ? (
            <Text style={styles.updated}>
              Updated {formatRelativeTime(dashboard.data.generated_at)}
            </Text>
          ) : null}
        </View>

        {dashboard.isLoading ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color={colors.greenDeep} />
            <Text style={styles.loadingText}>Running risk model...</Text>
          </View>
        ) : null}

        {dashboard.isError ? (
          <ApiErrorState
            error={dashboard.error}
            onRetry={() => dashboard.refetch()}
            isRetrying={dashboard.isRefetching}
          />
        ) : null}

        <View style={styles.card}>
          <View style={styles.cardHeading}>
            <View style={styles.iconWrap}>
              <Ionicons
                name="checkmark-circle-outline"
                size={20}
                color={colors.greenDeep}
              />
            </View>
            <Text style={styles.cardTitle}>Recommended Actions</Text>
          </View>
          {actions.map((action) => (
            <View key={action} style={styles.actionItem}>
              <Ionicons name="checkmark" size={15} color={colors.green} />
              <Text style={styles.actionText}>{action}</Text>
            </View>
          ))}
        </View>

        <View style={[styles.card, styles.noteCard]}>
          <View style={styles.cardHeading}>
            <Ionicons
              name="information-circle-outline"
              size={20}
              color={colors.greenDeep}
            />
            <Text style={styles.cardTitle}>What this number means</Text>
          </View>
          <Text style={styles.noteText}>
            The model combines recent weather with field-location features to
            estimate disease-favourable conditions. It is a crop-risk proxy,
            not a laboratory soil-health result.
          </Text>
          <Text style={styles.bands}>
            Bands: low &lt; 20 · moderate &lt; 60 · high ≥ 60 (placeholder
            thresholds).
          </Text>
        </View>

        <SoilReferenceCard soil={soil} />

        <PrimaryButton
          label="Ask AI About This Risk"
          icon="chatbubble-ellipses-outline"
          onPress={() => router.push("/chat" as never)}
        />

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Download Advisory Report"
          onPress={handleDownload}
          disabled={isDownloading}
          style={({ pressed }) => [styles.downloadSecondaryBtn, pressed && styles.pressed]}
        >
          {isDownloading ? (
            <ActivityIndicator size="small" color={colors.greenDeep} />
          ) : (
            <Ionicons name="document-text-outline" size={18} color={colors.greenDeep} />
          )}
          <Text style={styles.downloadSecondaryText}>
            {isDownloading ? "Generating Report..." : "Download Advisory Report (PDF)"}
          </Text>
        </Pressable>

        <View style={styles.footerNote}>
          <Ionicons name="leaf-outline" size={16} color={colors.greenDeep} />
          <Text style={styles.footerText}>
            For a lab-confirmed soil test, use the Soil Health Card scheme.
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
  gaugeCard: {
    borderRadius: radii.xl,
    padding: spacing.lg,
    alignItems: "center",
    borderWidth: 1,
    borderColor: colors.border,
  },
  eyebrow: {
    color: colors.textMuted,
    fontFamily: fonts.semibold,
    fontSize: 10,
    lineHeight: 14,
    letterSpacing: 0.8,
    marginBottom: spacing.md,
  },
  gaugeCaption: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
    textAlign: "center",
    marginTop: spacing.sm,
    maxWidth: 320,
  },
  updated: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
    marginTop: spacing.sm,
  },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.greenPale,
    borderRadius: radii.md,
    padding: spacing.md,
  },
  loadingText: {
    color: colors.textBody,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  cardHeading: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  iconWrap: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.greenSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.body,
    lineHeight: 22,
  },
  actionItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  actionText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
    flex: 1,
  },
  noteCard: {
    backgroundColor: colors.greenPale,
  },
  noteText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
  },
  bands: {
    color: colors.textMuted,
    fontFamily: fonts.medium,
    fontSize: 10,
    lineHeight: 15,
    marginTop: spacing.sm,
  },
  footerNote: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  footerText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    flex: 1,
  },
  downloadSecondaryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    backgroundColor: colors.card,
    borderWidth: 1.5,
    borderColor: colors.greenDeep,
    borderRadius: radii.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  downloadSecondaryText: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: sizes.body,
  },
  pressed: {
    opacity: 0.75,
  },
});
