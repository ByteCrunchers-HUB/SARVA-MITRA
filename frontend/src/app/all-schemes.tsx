import { Alert, Linking, StyleSheet, View } from "react-native";

import { GreenHeader } from "@/components/GreenHeader";
import { SchemeRow } from "@/components/SchemeRow";
import { Screen } from "@/components/Screen";
import { SCHEMES, type Scheme } from "@/data/schemes";
import { spacing } from "@/theme";

async function openScheme(scheme: Scheme) {
  try {
    await Linking.openURL(scheme.url);
  } catch {
    Alert.alert("Could not open link", "Please check your internet connection.");
  }
}

export default function AllSchemesScreen() {
  return (
    <Screen edges={["left", "right", "bottom"]}>
      <GreenHeader showBack title="All Schemes" />
      <View style={styles.body}>
        {SCHEMES.map((scheme) => (
          <SchemeRow
            key={scheme.id}
            scheme={scheme}
            onPress={() => openScheme(scheme)}
          />
        ))}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    padding: spacing.lg,
    gap: spacing.md,
  },
});
