import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { ApiError } from "@/api/client";
import { PrimaryButton } from "@/components/PrimaryButton";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

type ApiErrorStateProps = {
  error: unknown;
  onRetry: () => void;
  isRetrying?: boolean;
};

function describe(error: unknown): { title: string; message: string } {
  if (error instanceof ApiError) {
    if (error.kind === "network") {
      return {
        title: "Field engine unreachable",
        message: "Check your connection and the API URL in .env, then retry.",
      };
    }
    if (error.kind === "timeout") {
      return {
        title: "Taking longer than usual",
        message: "The field engine may be waking up. Please retry.",
      };
    }
    if (error.kind === "degraded") {
      return {
        title: "Some sources are unavailable",
        message: error.message,
      };
    }
    return { title: "Request failed", message: error.message };
  }

  return {
    title: "Something went wrong",
    message: error instanceof Error ? error.message : "Please retry.",
  };
}

export function ApiErrorState({
  error,
  onRetry,
  isRetrying = false,
}: ApiErrorStateProps) {
  const { title, message } = describe(error);

  return (
    <View style={styles.card}>
      <View style={styles.iconWrap}>
        <Ionicons name="cloud-offline-outline" size={26} color={colors.amberDark} />
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
      <PrimaryButton
        label={isRetrying ? "Retrying..." : "Try Again"}
        icon="refresh-outline"
        disabled={isRetrying}
        onPress={onRetry}
        style={styles.button}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    alignItems: "center",
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.amberSoft,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.md,
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
    textAlign: "center",
  },
  message: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  button: {
    alignSelf: "stretch",
    marginTop: spacing.lg,
    minHeight: 46,
  },
});
