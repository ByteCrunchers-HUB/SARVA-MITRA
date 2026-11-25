import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Alert, Linking, StyleSheet, Text, View } from "react-native";

import { GreenHeader } from "@/components/GreenHeader";
import { PrimaryButton } from "@/components/PrimaryButton";
import { SchemeRow } from "@/components/SchemeRow";
import { Screen } from "@/components/Screen";
import { SectionHeader } from "@/components/SectionHeader";
import { SCHEMES, type Scheme } from "@/data/schemes";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

async function openScheme(scheme: Scheme) {
  try {
    await Linking.openURL(scheme.url);
  } catch {
    Alert.alert("Could not open link", "Please check your internet connection.");
  }
}

export default function SchemesScreen() {
  return (
    <Screen edges={["left", "right"]}>
      <GreenHeader title="Government Schemes" />

      <View style={styles.body}>
        <View style={styles.hero}>
          <View style={styles.heroCopy}>
            <Text style={styles.heroEyebrow}>SUPPORT FOR FARMERS</Text>
            <Text style={styles.heroTitle}>Government Support for Farmers</Text>
            <Text style={styles.heroSub}>
              Get the right scheme for your needs.
            </Text>
          </View>
          <View style={styles.heroArt}>
            <Text style={styles.flag}>🇮🇳</Text>
            <Ionicons name="leaf" size={42} color={colors.green} />
          </View>
        </View>

        <SectionHeader title="Popular Schemes" />
        <View style={styles.list}>
          {SCHEMES.slice(0, 3).map((scheme) => (
            <SchemeRow
              key={scheme.id}
              scheme={scheme}
              onPress={() => openScheme(scheme)}
            />
          ))}
        </View>

        <PrimaryButton
          label="View All Schemes"
          icon="arrow-forward"
          onPress={() => router.push("/all-schemes" as never)}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    padding: spacing.lg,
    gap: spacing.lg,
  },
  hero: {
    minHeight: 150,
    borderRadius: radii.xl,
    backgroundColor: colors.greenPale,
    padding: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    overflow: "hidden",
  },
  heroCopy: {
    flex: 1,
  },
  heroEyebrow: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: 10,
    lineHeight: 14,
    letterSpacing: 0.7,
  },
  heroTitle: {
    color: colors.text,
    fontFamily: fonts.bold,
    fontSize: sizes.h2,
    lineHeight: 28,
    marginTop: 4,
    maxWidth: 220,
  },
  heroSub: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
    marginTop: 4,
  },
  heroArt: {
    width: 92,
    height: 92,
    borderRadius: 46,
    backgroundColor: colors.white,
    alignItems: "center",
    justifyContent: "center",
    gap: 2,
  },
  flag: {
    fontSize: 24,
  },
  list: {
    gap: spacing.md,
  },
});
