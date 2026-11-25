import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import {
  Animated,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Logo } from "@/components/Logo";
import { colors, fonts, sizes, spacing } from "@/theme";

export default function SplashRoute() {
  const insets = useSafeAreaInsets();
  const [progress] = useState(() => new Animated.Value(0));

  useEffect(() => {
    Animated.timing(progress, {
      toValue: 1,
      duration: 1700,
      useNativeDriver: false,
    }).start();

    const timer = setTimeout(() => {
      router.replace("/(tabs)" as never);
    }, 1950);

    return () => clearTimeout(timer);
  }, [progress]);

  const progressWidth = progress.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
  });

  return (
    <LinearGradient
      colors={[colors.greenDeep, "#0E6B25", colors.greenDeepEnd]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.root}
    >
      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <View style={[styles.content, { paddingTop: insets.top + 40 }]}>
        <View style={styles.logoWrap}>
          <Logo size={92} color={colors.white} accent={colors.greenBright} />
        </View>

        <Text style={styles.title}>Sarva Mitra</Text>
        <Text style={styles.tagline}>Smart Farming. Better Tomorrow.</Text>

        <View style={styles.leafRow}>
          <View style={styles.leafLine} />
          <Ionicons name="leaf-outline" size={18} color={colors.white70} />
          <View style={styles.leafLine} />
        </View>
      </View>

      <View style={[styles.bottom, { paddingBottom: insets.bottom + 34 }]}>
        <View style={styles.growingRow}>
          <Ionicons
            name="checkmark-circle"
            size={17}
            color={colors.greenBright}
          />
          <Text style={styles.growingText}>Growing a Greener India...</Text>
        </View>
        <View style={styles.progressTrack}>
          <Animated.View
            style={[styles.progressFill, { width: progressWidth }]}
          />
        </View>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    overflow: "hidden",
  },
  glowTop: {
    position: "absolute",
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: "rgba(87,184,90,0.16)",
    top: -110,
    right: -80,
  },
  glowBottom: {
    position: "absolute",
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: "rgba(255,255,255,0.06)",
    bottom: 80,
    left: -100,
  },
  content: {
    flex: 1,
    alignItems: "center",
    paddingHorizontal: spacing.xxl,
  },
  logoWrap: {
    width: 132,
    height: 132,
    borderRadius: 66,
    backgroundColor: "rgba(255,255,255,0.10)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 52,
    marginBottom: spacing.xl,
  },
  title: {
    color: colors.white,
    fontFamily: fonts.bold,
    fontSize: sizes.splash,
    lineHeight: 42,
    textAlign: "center",
  },
  tagline: {
    color: colors.white90,
    fontFamily: fonts.medium,
    fontSize: sizes.body,
    lineHeight: 24,
    textAlign: "center",
    marginTop: spacing.xs,
  },
  leafRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    marginTop: spacing.xxl,
  },
  leafLine: {
    width: 42,
    height: 1,
    backgroundColor: "rgba(255,255,255,0.30)",
  },
  bottom: {
    paddingHorizontal: spacing.xxl,
  },
  growingRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  growingText: {
    color: colors.white90,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  progressTrack: {
    height: 4,
    borderRadius: 2,
    backgroundColor: "rgba(255,255,255,0.20)",
    overflow: "hidden",
  },
  progressFill: {
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.greenBright,
  },
});
