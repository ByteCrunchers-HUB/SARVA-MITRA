import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { GreenHeader } from "@/components/GreenHeader";
import { PrimaryButton } from "@/components/PrimaryButton";
import {
  CROP_OPTIONS,
  LOCATION_PRESETS,
  STAGE_OPTIONS,
} from "@/data/locations";
import type { Crop, FarmConfig } from "@/api/types";
import { useFarmConfig, useSaveFarm } from "@/hooks/useFarmConfig";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

export default function FarmScreen() {
  const { farm, isLoading } = useFarmConfig();

  if (isLoading) {
    return (
      <SafeAreaView edges={["left", "right", "bottom"]} style={styles.root}>
        <GreenHeader showBack title="My Farm Details" />
        <View style={styles.loadingState}>
          <ActivityIndicator size="small" color={colors.greenDeep} />
          <Text style={styles.loadingText}>Loading farm details...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return <FarmForm initialFarm={farm} />;
}

function FarmForm({ initialFarm }: { initialFarm: FarmConfig }) {
  const saveFarm = useSaveFarm();
  const [form, setForm] = useState<FarmConfig>(initialFarm);
  const [latText, setLatText] = useState(String(initialFarm.lat));
  const [lonText, setLonText] = useState(String(initialFarm.lon));

  const update = (patch: Partial<FarmConfig>) =>
    setForm((current) => ({ ...current, ...patch }));

  const handleSave = async () => {
    const lat = Number(latText);
    const lon = Number(lonText);
    const name = form.name.trim();
    const location = form.location.trim();

    if (!name || !location) {
      Alert.alert("Missing details", "Enter a name and location for your farm.");
      return;
    }
    if (!Number.isFinite(lat) || lat < 6 || lat > 38) {
      Alert.alert("Invalid latitude", "Use a latitude between 6 and 38.");
      return;
    }
    if (!Number.isFinite(lon) || lon < 68 || lon > 98) {
      Alert.alert("Invalid longitude", "Use a longitude between 68 and 98.");
      return;
    }

    try {
      await saveFarm.mutateAsync({ ...form, name, location, lat, lon });
      Alert.alert("Farm details saved", "Your risk and advisory are now local to this farm.");
      router.back();
    } catch {
      Alert.alert("Could not save", "Please try again.");
    }
  };

  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.root}>
      <GreenHeader
        showBack
        title="My Farm Details"
        subtitle="Used for risk and advisory"
      />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.body}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Basic details</Text>
            <Text style={styles.label}>Farmer name</Text>
            <TextInput
              value={form.name}
              onChangeText={(text) => update({ name: text })}
              style={styles.input}
              placeholder="Your name"
              placeholderTextColor={colors.textMuted}
            />

            <Text style={styles.label}>Location name</Text>
            <TextInput
              value={form.location}
              onChangeText={(text) => update({ location: text })}
              style={styles.input}
              placeholder="Village / district"
              placeholderTextColor={colors.textMuted}
            />

            <Text style={styles.label}>Location presets</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chipRow}
            >
              {LOCATION_PRESETS.map((preset) => {
                const selected = form.location === preset.name;
                return (
                  <Pressable
                    key={preset.name}
                    accessibilityRole="button"
                    accessibilityLabel={`Use ${preset.name}`}
                    onPress={() =>
                      update({
                        location: preset.name,
                        lat: preset.lat,
                        lon: preset.lon,
                      })
                    }
                    style={[styles.chip, selected && styles.chipSelected]}
                  >
                    <Text
                      style={[styles.chipText, selected && styles.chipTextSelected]}
                    >
                      {preset.name}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            <View style={styles.coordRow}>
              <View style={styles.coordField}>
                <Text style={styles.label}>Latitude</Text>
                <TextInput
                  value={latText}
                  onChangeText={setLatText}
                  keyboardType="decimal-pad"
                  style={styles.input}
                  placeholder="16.98"
                  placeholderTextColor={colors.textMuted}
                />
              </View>
              <View style={styles.coordField}>
                <Text style={styles.label}>Longitude</Text>
                <TextInput
                  value={lonText}
                  onChangeText={setLonText}
                  keyboardType="decimal-pad"
                  style={styles.input}
                  placeholder="82.24"
                  placeholderTextColor={colors.textMuted}
                />
              </View>
            </View>
          </View>

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Crop</Text>
            <View style={styles.optionGrid}>
              {CROP_OPTIONS.map((crop) => {
                const selected = form.crop === crop.id;
                return (
                  <Pressable
                    key={crop.id}
                    accessibilityRole="button"
                    accessibilityLabel={`Select ${crop.label}`}
                    onPress={() => update({ crop: crop.id as Crop })}
                    style={[styles.option, selected && styles.optionSelected]}
                  >
                    <Text
                      style={[styles.optionText, selected && styles.optionTextSelected]}
                    >
                      {crop.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={styles.sectionTitleSpaced}>Growth stage</Text>
            <View style={styles.optionGrid}>
              {STAGE_OPTIONS.map((stage) => {
                const selected = form.stage === stage.id;
                return (
                  <Pressable
                    key={stage.id}
                    accessibilityRole="button"
                    accessibilityLabel={`Select ${stage.label}`}
                    onPress={() => update({ stage: stage.id })}
                    style={[styles.option, selected && styles.optionSelected]}
                  >
                    <Text
                      style={[styles.optionText, selected && styles.optionTextSelected]}
                    >
                      {stage.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          <View style={styles.note}>
            <Ionicons name="information-circle-outline" size={16} color={colors.greenDeep} />
            <Text style={styles.noteText}>
              Coordinates are snapped to the nearest trained grid point. The
              model accepts India latitudes 6–38 and longitudes 68–98.
            </Text>
          </View>

          <PrimaryButton
            label={saveFarm.isPending ? "Saving..." : "Save Farm Details"}
            icon={saveFarm.isPending ? undefined : "checkmark-circle-outline"}
            disabled={saveFarm.isPending}
            onPress={handleSave}
          />
          {saveFarm.isPending ? (
            <View style={styles.savingRow}>
              <ActivityIndicator size="small" color={colors.greenDeep} />
            </View>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.page,
  },
  loadingState: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
  },
  loadingText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  flex: {
    flex: 1,
  },
  body: {
    padding: spacing.lg,
    gap: spacing.lg,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  sectionTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
    marginBottom: spacing.md,
  },
  sectionTitleSpaced: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  label: {
    color: colors.textBody,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
    marginBottom: 6,
  },
  input: {
    backgroundColor: colors.page,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 11,
    color: colors.text,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
    marginBottom: spacing.md,
  },
  chipRow: {
    gap: spacing.sm,
    paddingRight: spacing.sm,
    marginBottom: spacing.md,
  },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: colors.page,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipSelected: {
    backgroundColor: colors.greenDeep,
    borderColor: colors.greenDeep,
  },
  chipText: {
    color: colors.textBody,
    fontFamily: fonts.medium,
    fontSize: 11,
    lineHeight: 16,
  },
  chipTextSelected: {
    color: colors.white,
  },
  coordRow: {
    flexDirection: "row",
    gap: spacing.md,
  },
  coordField: {
    flex: 1,
  },
  optionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  option: {
    minWidth: 92,
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
    borderRadius: radii.md,
    backgroundColor: colors.page,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
  },
  optionSelected: {
    backgroundColor: colors.greenSoft,
    borderColor: colors.green,
  },
  optionText: {
    color: colors.textBody,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  optionTextSelected: {
    color: colors.greenDeep,
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
  savingRow: {
    alignItems: "center",
    marginTop: -spacing.md,
  },
});
