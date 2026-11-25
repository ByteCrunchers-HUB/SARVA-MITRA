import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { sendChat } from "@/api/client";
import { ActionTile } from "@/components/ActionTile";
import { AdvisoryCard } from "@/components/AdvisoryCard";
import { ApiErrorState } from "@/components/ApiErrorState";
import { GreenHeader } from "@/components/GreenHeader";
import { IconButton } from "@/components/IconButton";
import { LiveBadge } from "@/components/LiveBadge";
import { MetricTile } from "@/components/MetricTile";
import { RiskCard } from "@/components/RiskCard";
import { Screen } from "@/components/Screen";
import { SectionHeader } from "@/components/SectionHeader";
import { SoilReferenceCard } from "@/components/SoilReferenceCard";
import { Sparkline } from "@/components/Sparkline";
import { useDashboard } from "@/hooks/useDashboard";
import { useFarmConfig } from "@/hooks/useFarmConfig";
import { soilReferenceForFarm } from "@/data/soilSnapshot";
import { getLatestAdvisoryText, saveLatestAdvisoryText } from "@/store/chat";
import { cleanAssistantText, downloadAdvisoryReport } from "@/utils/report";
import { colors, fonts, radii, shadows, sizes, spacing } from "@/theme";
import {
  deriveCondition,
  formatNumber,
  formatRelativeTime,
} from "@/utils/format";

export default function HomeScreen() {
  const { farm } = useFarmConfig();
  const dashboard = useDashboard(farm);
  const soil = soilReferenceForFarm(farm);
  const firstName = farm.name.split(" ")[0] || "Farmer";

  const data = dashboard.data;
  const telemetry = data?.current_telemetry;
  const risk = data?.ml_risk;
  const trends = data?.historical_trends ?? [];
  const moisture = trends
    .slice(-8)
    .map((record) => record.soil_moisture_pct)
    .filter((value) => Number.isFinite(value));
  const badgeLabel =
    data?.status === "degraded"
      ? "Partial"
      : data
        ? "Live"
        : "Awaiting API";

  const [isDownloadingReport, setIsDownloadingReport] = useState(false);

  // Automatically pre-fetch complete agronomic assessment report in the background, matching Web UI process
  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const cached = await getLatestAdvisoryText(farm.crop, farm.stage);
        if (!cached || cached.length < 200) {
          const res = await sendChat({
            question: `Provide a complete agronomic status assessment and recommendations for ${farm.crop} (${farm.stage}) based on current field conditions.`,
            crop: farm.crop,
            lat: farm.lat,
            lon: farm.lon,
            location: farm.location,
            stage: farm.stage,
            chat_history: [],
            mode: "report",
          });
          if (active && res?.answer) {
            const cleaned = cleanAssistantText(res.answer);
            if (cleaned.length >= 200) {
              await saveLatestAdvisoryText(farm.crop, farm.stage, cleaned);
            }
          }
        }
      } catch {
        // Non-blocking background sync
      }
    })();
    return () => {
      active = false;
    };
  }, [farm.crop, farm.lat, farm.location, farm.lon, farm.stage]);

  const handleDownloadReport = async () => {
    if (isDownloadingReport) return;
    setIsDownloadingReport(true);
    try {
      await downloadAdvisoryReport({
        farm,
      });
    } finally {
      setIsDownloadingReport(false);
    }
  };

  const go = (path: string) => router.push(path as never);

  return (
    <Screen
      edges={["left", "right"]}
      refreshControl={
        <RefreshControl
          refreshing={dashboard.isRefetching}
          onRefresh={() => {
            void dashboard.refetch();
          }}
          tintColor={colors.greenDeep}
          colors={[colors.green]}
        />
      }
    >
      <GreenHeader
        title="Sarva Mitra"
        subtitle={farm.location}
        left={
          <IconButton
            accessibilityLabel="Open menu"
            name="menu-outline"
            onPress={() => go("/(tabs)/profile")}
          />
        }
        right={
          <IconButton
            accessibilityLabel="Open notifications"
            name="notifications-outline"
            onPress={() => go("/notifications")}
          />
        }
      />

      <View style={styles.body}>
        <View style={[styles.greetingCard, shadows.card]}>
          <View style={styles.greetingCopy}>
            <Text style={styles.greeting}>Hello, {firstName}! 👋</Text>
            <Text style={styles.greetingSub}>
              Let’s make your farm healthier together.
            </Text>
          </View>
          <View style={styles.avatar}>
            <Ionicons name="person" size={30} color={colors.greenDeep} />
            <View style={styles.avatarLeaf}>
              <Ionicons name="leaf" size={11} color={colors.white} />
            </View>
          </View>
        </View>

        <View style={styles.weatherCard}>
          <View style={styles.weatherItem}>
            <Ionicons name="location-outline" size={18} color={colors.white} />
            <Text style={styles.weatherText} numberOfLines={1}>
              {data?.location?.name || farm.location}
            </Text>
          </View>
          <View style={styles.weatherDivider} />
          <View style={styles.weatherItem}>
            <Ionicons name="sunny-outline" size={18} color={colors.amber} />
            <Text style={styles.weatherText}>
              {formatNumber(telemetry?.temperature_c)}°C
            </Text>
            <Text style={styles.weatherMuted}>
              {telemetry ? deriveCondition(telemetry.rainfall_mm, telemetry.sunlight_wm2) : "—"}
            </Text>
          </View>
        </View>

        <View style={styles.metaRow}>
          <Text style={styles.updatedText}>
            {data ? `Updated ${formatRelativeTime(data.generated_at)}` : "Connecting to field engine..."}
          </Text>
          {telemetry?.source ? (
            <Text style={styles.sourceText} numberOfLines={1}>
              {telemetry.source}
            </Text>
          ) : null}
        </View>

        {dashboard.isLoading ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color={colors.greenDeep} />
            <Text style={styles.loadingText}>Reading live field data...</Text>
          </View>
        ) : null}

        {dashboard.isError ? (
          <ApiErrorState
            error={dashboard.error}
            onRetry={() => dashboard.refetch()}
            isRetrying={dashboard.isRefetching}
          />
        ) : null}

        {data?.status === "degraded" ? (
          <View style={styles.degradedBanner}>
            <Ionicons name="warning-outline" size={17} color={colors.amberDark} />
            <Text style={styles.degradedText}>
              Some data sources are temporarily unavailable.
            </Text>
          </View>
        ) : null}

        <SectionHeader
          title="Live Soil Data"
          right={
            <LiveBadge
              label={badgeLabel}
              tone={data ? "live" : "pending"}
            />
          }
        />

        <View style={styles.metricRow}>
          <MetricTile
            icon="water-outline"
            label="Moisture"
            value={formatNumber(telemetry?.soil_moisture_pct)}
            unit="%"
            caption="Live reading"
            tint={colors.blueSoft}
            iconColor={colors.blue}
          />
          <MetricTile
            icon="thermometer-outline"
            label="Air Temp"
            value={formatNumber(telemetry?.temperature_c)}
            unit="°C"
            caption="Live reading"
            tint={colors.redSoft}
            iconColor={colors.red}
          />
        </View>
        <View style={styles.metricRow}>
          <MetricTile
            icon="stats-chart-outline"
            label="Humidity"
            value={formatNumber(telemetry?.humidity_pct)}
            unit="%"
            caption="Live reading"
            tint={colors.greenSoft}
            iconColor={colors.greenDeep}
          />
          <MetricTile
            icon="sunny-outline"
            label="Sunlight"
            value={formatNumber(telemetry?.sunlight_wm2)}
            unit="W/m²"
            caption="Live reading"
            tint={colors.amberSoft}
            iconColor={colors.amberDark}
          />
        </View>

        <RiskCard
          riskPct={risk?.risk_pct ?? null}
          riskLevel={risk?.risk_level}
          onPress={() => go("/(tabs)/predict")}
        />

        <AdvisoryCard
          text={
            data?.quick_advisory ||
            "An advisory will appear once the field engine responds."
          }
          onAskAssistant={() => go("/chat")}
          onDownloadReport={handleDownloadReport}
          isDownloading={isDownloadingReport}
        />

        <SectionHeader
          title="8-Day Moisture Trend"
          right={
            moisture.length > 1 ? (
              <Text style={styles.trendMeta}>
                {formatNumber(Math.min(...moisture))}–{formatNumber(Math.max(...moisture))}%
              </Text>
            ) : (
              <Text style={styles.trendMeta}>—</Text>
            )
          }
        />
        <View style={styles.trendCard}>
          {moisture.length > 1 ? (
            <Sparkline values={moisture} color={colors.green} fillId="moistureSpark" />
          ) : (
            <View style={styles.trendEmpty}>
              <Ionicons name="analytics-outline" size={22} color={colors.textMuted} />
              <Text style={styles.trendEmptyText}>Not enough history yet</Text>
            </View>
          )}
          <View style={styles.trendLabels}>
            <Text style={styles.trendLabel}>Older</Text>
            <Text style={styles.trendLabel}>Recent</Text>
          </View>
        </View>

        <SoilReferenceCard soil={soil} />

        <SectionHeader title="Quick actions" />
        <View style={styles.actionRow}>
          <ActionTile
            icon="leaf-outline"
            label="Crop Risk"
            onPress={() => go("/(tabs)/predict")}
          />
          <ActionTile
            icon="chatbubble-ellipses-outline"
            label="AI Assistant"
            tint={colors.blueSoft}
            iconColor={colors.blue}
            onPress={() => go("/chat")}
          />
        </View>
        <View style={styles.actionRow}>
          <ActionTile
            icon="stats-chart-outline"
            label="History"
            tint={colors.amberSoft}
            iconColor={colors.amberDark}
            onPress={() => go("/(tabs)/history")}
          />
          <ActionTile
            icon="business-outline"
            label="Schemes"
            tint={colors.greenSoft}
            iconColor={colors.greenDeep}
            onPress={() => go("/(tabs)/schemes")}
          />
        </View>

        <View style={styles.footnote}>
          <Ionicons
            name="information-circle-outline"
            size={16}
            color={colors.greenDeep}
          />
          <Text style={styles.footnoteText}>
            Crop risk is a weather-based disease proxy, not a soil test.
          </Text>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    gap: spacing.md,
  },
  greetingCard: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    padding: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  greetingCopy: {
    flex: 1,
  },
  greeting: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
  },
  greetingSub: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
    marginTop: 3,
  },
  avatar: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: colors.greenSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarLeaf: {
    position: "absolute",
    right: -2,
    bottom: 1,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: colors.green,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: colors.card,
  },
  weatherCard: {
    backgroundColor: colors.greenDeep,
    borderRadius: radii.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  weatherItem: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  weatherDivider: {
    width: 1,
    height: 26,
    backgroundColor: "rgba(255,255,255,0.22)",
  },
  weatherText: {
    color: colors.white,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  weatherMuted: {
    color: colors.white70,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
    marginLeft: 2,
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    marginTop: -4,
  },
  updatedText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
  },
  sourceText: {
    color: colors.greenDeep,
    fontFamily: fonts.medium,
    fontSize: 10,
    lineHeight: 14,
    maxWidth: "42%",
    textAlign: "right",
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
  degradedBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.amberSoft,
    borderRadius: radii.md,
    padding: spacing.md,
  },
  degradedText: {
    color: colors.amberDark,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
    flex: 1,
  },
  metricRow: {
    flexDirection: "row",
    gap: spacing.md,
  },
  trendMeta: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: sizes.tiny,
    lineHeight: 16,
  },
  trendCard: {
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  trendLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 2,
  },
  trendLabel: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
  },
  trendEmpty: {
    height: 72,
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  trendEmptyText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  actionRow: {
    flexDirection: "row",
    gap: spacing.md,
  },
  footnote: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.greenPale,
    borderRadius: radii.md,
    padding: spacing.md,
    marginTop: spacing.sm,
  },
  footnoteText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    flex: 1,
  },
});
