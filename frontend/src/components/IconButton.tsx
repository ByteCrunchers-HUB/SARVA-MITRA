import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fonts } from "@/theme";

type IconButtonProps = {
  name: React.ComponentProps<typeof Ionicons>["name"];
  onPress?: () => void;
  color?: string;
  badge?: number;
  accessibilityLabel: string;
  disabled?: boolean;
};

export function IconButton({
  name,
  onPress,
  color = colors.white,
  badge,
  accessibilityLabel,
  disabled = false,
}: IconButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      disabled={disabled}
      hitSlop={10}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        pressed && !disabled && styles.pressed,
        disabled && { opacity: 0.6 },
      ]}
    >
      <Ionicons name={name} size={22} color={color} />
      {badge ? (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{badge > 9 ? "9+" : badge}</Text>
        </View>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  pressed: {
    opacity: 0.7,
  },
  badge: {
    position: "absolute",
    top: 5,
    right: 4,
    minWidth: 15,
    height: 15,
    paddingHorizontal: 3,
    borderRadius: 8,
    backgroundColor: colors.red,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    color: colors.white,
    fontFamily: fonts.bold,
    fontSize: 9,
    lineHeight: 11,
  },
});
