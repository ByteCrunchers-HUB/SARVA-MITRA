import AsyncStorage from "@react-native-async-storage/async-storage";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { GreenHeader } from "@/components/GreenHeader";
import { Screen } from "@/components/Screen";
import { useFarmConfig } from "@/hooks/useFarmConfig";
import { colors, fonts, radii, shadows, sizes, spacing } from "@/theme";

type MenuRowProps = {
  icon: React.ComponentProps<typeof Ionicons>["name"];
  label: string;
  value?: string;
  onPress?: () => void;
  destructive?: boolean;
  disabled?: boolean;
};

function MenuRow({
  icon,
  label,
  value,
  onPress,
  destructive = false,
  disabled = false,
}: MenuRowProps) {
  const color = destructive ? colors.red : colors.text;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.menuRow,
        pressed && !disabled && styles.pressed,
        disabled && styles.disabled,
      ]}
    >
      <Ionicons
        name={icon}
        size={20}
        color={destructive ? colors.red : colors.greenDeep}
      />
      <Text style={[styles.menuLabel, { color }]}>{label}</Text>
      {value ? <Text style={styles.menuValue}>{value}</Text> : null}
      <Ionicons
        name="chevron-forward"
        size={17}
        color={colors.textMuted}
      />
    </Pressable>
  );
}

export default function ProfileScreen() {
  const { farm } = useFarmConfig();

  const handleLogout = () => {
    Alert.alert(
      "Logout",
      "This clears local farm and chat data on this device.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Clear",
          style: "destructive",
          onPress: async () => {
            await AsyncStorage.clear();
            router.replace("/(tabs)" as never);
          },
        },
      ],
    );
  };

  return (
    <Screen edges={["left", "right"]}>
      <GreenHeader title="Profile & Settings" />

      <View style={styles.body}>
        <View style={[styles.profileCard, shadows.card]}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={34} color={colors.greenDeep} />
          </View>
          <View style={styles.profileCopy}>
            <Text style={styles.name}>{farm.name}</Text>
            <View style={styles.locationRow}>
              <Ionicons
                name="location-outline"
                size={13}
                color={colors.textMuted}
              />
              <Text style={styles.location}>{farm.location}</Text>
            </View>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Edit farm details"
            onPress={() => router.push("/farm" as never)}
            style={styles.editPill}
          >
            <Text style={styles.editText}>Edit</Text>
          </Pressable>
        </View>

        <View style={styles.menu}>
          <MenuRow
            icon="location-outline"
            label="My Farm Details"
            onPress={() => router.push("/farm" as never)}
          />
          <MenuRow
            icon="notifications-outline"
            label="Notification Settings"
            value="On"
            disabled
          />
          <MenuRow
            icon="language-outline"
            label="Language"
            value="English"
            disabled
          />
          <MenuRow
            icon="information-circle-outline"
            label="About Sarva Mitra"
            onPress={() => router.push("/about" as never)}
          />
          <MenuRow
            icon="help-circle-outline"
            label="Help & Support"
            onPress={() => router.push("/help" as never)}
          />
          <MenuRow
            icon="shield-checkmark-outline"
            label="Privacy Policy"
            onPress={() => router.push("/privacy" as never)}
          />
          <MenuRow
            icon="log-out-outline"
            label="Logout"
            destructive
            onPress={handleLogout}
          />
        </View>

        <Text style={styles.footer}>Sarva Mitra · Smart Farming, Better Tomorrow</Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    padding: spacing.lg,
    gap: spacing.lg,
  },
  profileCard: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    padding: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  avatar: {
    width: 62,
    height: 62,
    borderRadius: 31,
    backgroundColor: colors.greenSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  profileCopy: {
    flex: 1,
  },
  name: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
  },
  locationRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    marginTop: 3,
  },
  location: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
  },
  editPill: {
    paddingHorizontal: spacing.md,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: colors.greenSoft,
  },
  editText: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: 11,
    lineHeight: 16,
  },
  menu: {
    backgroundColor: colors.card,
    borderRadius: radii.xl,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  menuRow: {
    minHeight: 54,
    paddingHorizontal: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  pressed: {
    backgroundColor: colors.greenPale,
  },
  disabled: {
    opacity: 0.55,
  },
  menuLabel: {
    flex: 1,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  menuValue: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
  },
  footer: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 15,
    textAlign: "center",
    marginTop: spacing.sm,
  },
});
