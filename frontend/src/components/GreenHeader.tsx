import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import type { ReactNode } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { colors, fonts, sizes, spacing } from "@/theme";

type GreenHeaderProps = {
  title: string;
  subtitle?: string;
  left?: ReactNode;
  right?: ReactNode;
  showBack?: boolean;
  onBack?: () => void;
  children?: ReactNode;
};

export function GreenHeader({
  title,
  subtitle,
  left,
  right,
  showBack = false,
  onBack,
  children,
}: GreenHeaderProps) {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const handleBack = () => {
    if (onBack) {
      onBack();
      return;
    }
    if (router.canGoBack()) {
      router.back();
      return;
    }
    router.replace("/(tabs)" as never);
  };

  return (
    <LinearGradient
      colors={[colors.greenDeep, "#0E6B25", colors.greenDeepEnd]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.root, { paddingTop: insets.top + spacing.sm }]}
    >
      <View style={styles.row}>
        <View style={styles.side}>
          {left ??
            (showBack ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Go back"
                hitSlop={10}
                onPress={handleBack}
                style={({ pressed }) => [
                  styles.iconButton,
                  pressed && styles.pressed,
                ]}
              >
                <Ionicons name="arrow-back" size={22} color={colors.white} />
              </Pressable>
            ) : null)}
        </View>

        <View style={styles.titleWrap}>
          <Text numberOfLines={1} style={styles.title}>
            {title}
          </Text>
          {subtitle ? (
            <Text numberOfLines={2} style={styles.subtitle}>
              {subtitle}
            </Text>
          ) : null}
        </View>

        <View style={[styles.side, styles.right]}>{right}</View>
      </View>
      {children}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  root: {
    paddingBottom: spacing.lg,
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
  },
  row: {
    minHeight: 44,
    paddingHorizontal: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
  },
  side: {
    width: 44,
    alignItems: "flex-start",
  },
  right: {
    alignItems: "flex-end",
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  pressed: {
    opacity: 0.7,
  },
  titleWrap: {
    flex: 1,
    alignItems: "center",
    paddingHorizontal: spacing.sm,
  },
  title: {
    color: colors.white,
    fontFamily: fonts.semibold,
    fontSize: sizes.h2,
    lineHeight: 28,
    textAlign: "center",
  },
  subtitle: {
    color: colors.white70,
    fontFamily: fonts.regular,
    fontSize: sizes.tiny,
    lineHeight: 16,
    textAlign: "center",
    marginTop: 2,
  },
});
