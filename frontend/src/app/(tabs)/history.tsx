import { Ionicons } from "@expo/vector-icons";
import {
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { ApiErrorState } from "@/components/ApiErrorState";
import { BarChart } from "@/components/BarChart";
import { GreenHeader } from "@/components/GreenHeader";
import { Screen } from "@/components/Screen";
import { SectionHeader } from "@/components/SectionHeader";
import { Sparkline } from "@/components/Sparkline";
import { useDashboard } from "@/hooks/useDashboard";
import { useFarmConfig } from "@/hooks/useFarmConfig";
import { useRiskTrend } from "@/hooks/useRiskTrend";
import { colors, fonts, radii, sizes, spacing } from "@/theme";
import {
  formatNumber,
  riskColor,
  riskLabel,
  riskSoftColor,
} from "@/utils/format";

function average(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function shortDate(iso: string): string {
  return iso.length >= 10 ? iso.slice(5) : iso;
}

export default function HistoryScreen() {
  const { farm } = useFarmConfig();
  const dashboard = useDashboard(farm);
  const riskTrend = useRiskTrend(farm);

  const days = dashboard.data?.historical_trends.slice(-8) ?? [];
  const moisture = days
    .map((day) => day.soil_moisture_pct)
    .filter((value) => Number.isFinite(value));
  const temperatures = days
    .map((day) => day.air_temperature_c)
    .filter((value) => Number.isFinite(value));
  const rainfall = days
    .map((day) => day.rainfall_mm)
    .filter((value) => Number.isFinite(value));
  const riskPoints = riskTrend.data ?? [];
  const risks = riskPoints.map((point) => point.risk_pct);

  const avgRisk = average(risks) ?? dashboard.data?.ml_risk.risk_pct ?? null;
  const avgMoisture = average(moisture);
  const totalRain = rainfall.reduce((sum, value) => sum + value, 0);

  const refresh = () => {
    void dashboard.refetch();
    void riskTrend.refetch();
  };

  const dayMap = new Map(days.map((day) => [day.date, day]));
  const recent = [...riskPoints].reverse().slice(0, 5);

  return (
    <Screen
      edges={["left", "right"]}
      refreshControl={
        <RefreshControl
          refreshing={dashboard.isRefetching || riskTrend.isRefetching}
          onRefresh={refresh}
          tintColor={colors.greenDeep}
          colors={[colors.green]}
        />
      }
    >
      <GreenHeader
        title="History & Analytics"
        subtitle={`${farm.location} · ${farm.crop}`}
      />

      <View style={styles.body}>
        <View style={styles.summaryRow}>
          <View style={[styles.summaryCard, { backgroundColor: riskSoftColor(avgRisk == null ? undefined : avgRisk < 60 ? (avgRisk < 20 ? "low" : "moderate") : "high") }]}>
            <Ionicons name="shield-half-outline" size={18} color={riskColor(avgRisk == null ? undefined : avgRisk < 20 ? "low" : avgRisk < 60 ? "moderate" : "high")} />
            <Text style={styles.summaryLabel}>Avg Risk</Text>
            <Text style={styles.summaryValue}>
              {avgRisk == null ? "—" : `${Math.round(avgRisk)}%`}
            </Text>
          </View>
          <View style={[styles.summaryCard, { backgroundColor: colors.blueSoft }]}>
            <Ionicons name="water-outline" size={18} color={colors.blue} />
            <Text style={styles.summaryLabel}>Avg Moisture</Text>
            <Text style={styles.summaryValue}>
              {formatNumber(avgMoisture)}%
            </Text>
          </View>
          <View style={[styles.summaryCard, { backgroundColor: colors.amberSoft }]}>
            <Ionicons name="rainy-outline" size={18} color={colors.amberDark} />
            <Text style={styles.summaryLabel}>8-Day Rain</Text>
            <Text style={styles.summaryValue}>
              {formatNumber(totalRain, 1)} mm
            </Text>
          </View>
        </View>

        {dashboard.isError ? (
          <ApiErrorState
            error={dashboard.error}
            onRetry={() => dashboard.refetch()}
            isRetrying={dashboard.isRefetching}
          />
        ) : null}

        {dashboard.isLoading || riskTrend.isLoading ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color={colors.greenDeep} />
            <Text style={styles.loadingText}>Building analytics...</Text>
          </View>
        ) : null}

        <SectionHeader title="Crop Risk Trend" />
        <View style={styles.card}>
          {riskTrend.isError ? (
            <View style={styles.inlineError}>
              <Ionicons name="warning-outline" size={18} color={colors.amberDark} />
              <Text style={styles.inlineErrorText}>
                Risk history is unavailable. Pull down to retry.
              </Text>
            </View>
          ) : risks.length > 1 ? (
            <>
              <Sparkline
                values={risks}
                color={colors.green}
                fillId="riskTrendFill"
              />
              <View style={styles.chartLabels}>
                <Text style={styles.chartLabel}>
                  {shortDate(riskPoints[0].date)}
                </Text>
                <Text style={styles.chartLabel}>
                  {shortDate(riskPoints[riskPoints.length - 1].date)}
                </Text>
              </View>
            </>
          ) : (
            <View style={styles.emptyChart}>
              <Ionicons name="analytics-outline" size={24} color={colors.textMuted} />
              <Text style={styles.emptyText}>Not enough history for a trend.</Text>
            </View>
          )}
        </View>

        <SectionHeader title="Soil Moisture" />
        <View style={styles.card}>
          {moisture.length > 1 ? (
            <>
              <Sparkline
                values={moisture}
                color={colors.blue}
                fillId="moistureTrendFill"
              />
              <View style={styles.chartLabels}>
                <Text style={styles.chartLabel}>
                  {shortDate(days[0].date)}
                </Text>
                <Text style={styles.chartLabel}>
                  {shortDate(days[days.length - 1].date)}
                </Text>
              </View>
            </>
          ) : (
            <View style={styles.emptyChart}>
              <Text style={styles.emptyText}>No soil moisture history yet.</Text>
            </View>
          )}
        </View>

        <SectionHeader title="Rainfall" />
        <View style={styles.card}>
          {rainfall.length > 0 ? (
            <BarChart values={rainfall} color={colors.blue} labels={days.map((d) => shortDate(d.date))} />
          ) : (
            <View style={styles.emptyChart}>
              <Text style={styles.emptyText}>No rainfall history yet.</Text>
            </View>
          )}
        </View>

        <SectionHeader title="Air Temperature" />
        <View style={styles.card}>
          {temperatures.length > 1 ? (
            <Sparkline
              values={temperatures}
              color={colors.red}
              fillId="temperatureTrendFill"
            />
          ) : (
            <View style={styles.emptyChart}>
              <Text style={styles.emptyText}>No temperature history yet.</Text>
            </View>
          )}
        </View>

        <SectionHeader title="Recent Predictions" />
        {recent.length > 0 ? (
          <View style={styles.card}>
            {recent.map((point, index) => {
              const day = dayMap.get(point.date);
              const level = point.risk_level;
              return (
                <View
                  key={point.date}
                  style={[
                    styles.recentRow,
                    index === recent.length - 1 && styles.recentRowLast,
                  ]}
                >
                  <View style={styles.recentDate}>
                    <Text style={styles.recentDateText}>
                      {shortDate(point.date)}
                    </Text>
                  </View>
                  <View style={styles.recentInfo}>
                    <Text style={styles.recentTitle}>
                      Risk {Math.round(point.risk_pct)}%
                    </Text>
                    <Text style={styles.recentSub}>
                      Moisture {formatNumber(day?.soil_moisture_pct)}%
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.levelPill,
                      { backgroundColor: riskSoftColor(level) },
                    ]}
                  >
                    <Text style={[styles.levelText, { color: riskColor(level) }]}>
                      {riskLabel(level)}
                    </Text>
                  </View>
                </View>
              );
            })}
          </View>
        ) : (
          <View style={styles.card}>
            <View style={styles.emptyChart}>
              <Text style={styles.emptyText}>No reconstructed risk points yet.</Text>
            </View>
          </View>
        )}

        <View style={styles.note}>
          <Ionicons name="information-circle-outline" size={15} color={colors.greenDeep} />
          <Text style={styles.noteText}>
            Risk history is reconstructed from 7-day weather windows using the
            ML API. It is cached for 6 hours.
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
  summaryRow: {
    flexDirection: "row",
    gap: spacing.md,
  },
  summaryCard: {
    flex: 1,
    minHeight: 110,
    borderRadius: radii.lg,
    padding: spacing.md,
    justifyContent: "space-between",
  },
  summaryLabel: {
    color: colors.textBody,
    fontFamily: fonts.medium,
    fontSize: 10,
    lineHeight: 14,
    marginTop: spacing.sm,
  },
  summaryValue: {
    color: colors.text,
    fontFamily: fonts.bold,
    fontSize: 18,
    lineHeight: 24,
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
  inlineError: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.sm,
  },
  inlineErrorText: {
    color: colors.amberDark,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
    flex: 1,
  },
  chartLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 2,
  },
  chartLabel: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
  },
  emptyChart: {
    height: 72,
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  emptyText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
    textAlign: "center",
  },
  recentRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  recentRowLast: {
    borderBottomWidth: 0,
  },
  recentDate: {
    width: 52,
    height: 52,
    borderRadius: 14,
    backgroundColor: colors.greenPale,
    alignItems: "center",
    justifyContent: "center",
  },
  recentDateText: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: 11,
    lineHeight: 16,
  },
  recentInfo: {
    flex: 1,
  },
  recentTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  recentSub: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    marginTop: 2,
  },
  levelPill: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: 999,
  },
  levelText: {
    fontFamily: fonts.semibold,
    fontSize: 10,
    lineHeight: 14,
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
