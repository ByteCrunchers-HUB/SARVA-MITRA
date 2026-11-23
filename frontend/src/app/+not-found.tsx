import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "@/components/PrimaryButton";
import { Screen } from "@/components/Screen";
import { colors, fonts, sizes, spacing } from "@/theme";

export default function NotFoundScreen() {
  return (
    <Screen edges={["top", "left", "right", "bottom"]}>
      <View style={styles.body}>
        <Text style={styles.code}>404</Text>
        <Text style={styles.title}>This field is empty.</Text>
        <Text style={styles.subtitle}>
          The screen you are looking for does not exist.
        </Text>
        <PrimaryButton
          label="Back to Home"
          icon="home-outline"
          onPress={() => router.replace("/(tabs)" as never)}
          style={styles.button}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.xxl,
  },
  code: {
    color: colors.greenSoft,
    fontFamily: fonts.bold,
    fontSize: 72,
    lineHeight: 80,
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h2,
    lineHeight: 28,
  },
  subtitle: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.body,
    lineHeight: 22,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  button: {
    marginTop: spacing.xl,
    alignSelf: "stretch",
  },
});
