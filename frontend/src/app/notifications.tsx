import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useCallback, useState } from "react";

import { GreenHeader } from "@/components/GreenHeader";
import { Screen } from "@/components/Screen";
import { NOTIFICATIONS, type NotificationTone } from "@/data/notifications";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

const TONES: Record<
  NotificationTone,
  { tint: string; color: string }
> = {
  risk: { tint: colors.redSoft, color: colors.red },
  scheme: { tint: colors.greenSoft, color: colors.greenDeep },
  weather: { tint: colors.blueSoft, color: colors.blue },
  tip: { tint: colors.amberSoft, color: colors.amberDark },
};

export default function NotificationsScreen() {
  const [readIds, setReadIds] = useState<string[]>([]);
  const unread = NOTIFICATIONS.length - readIds.length;

  const toggleRead = useCallback((id: string) => {
    setReadIds((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id],
    );
  }, []);

  return (
    <Screen edges={["left", "right", "bottom"]}>
      <GreenHeader
        showBack
        title="Notifications"
        subtitle={unread > 0 ? `${unread} unread update${unread === 1 ? "" : "s"}` : "All caught up"}
        right={
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Mark all as read"
            onPress={() => setReadIds(NOTIFICATIONS.map((item) => item.id))}
            style={({ pressed }) => [styles.markRead, pressed && styles.pressed]}
          >
            <Text style={styles.markReadText}>Read all</Text>
          </Pressable>
        }
      />

      <View style={styles.body}>
        <View style={styles.summaryCard}>
          <Ionicons name="notifications-outline" size={22} color={colors.greenDeep} />
          <View style={styles.summaryCopy}>
            <Text style={styles.summaryTitle}>Field updates</Text>
            <Text style={styles.summaryText}>
              Risk alerts, weather changes and scheme reminders in one place.
            </Text>
          </View>
        </View>

        {NOTIFICATIONS.map((item) => {
          const tone = TONES[item.tone];
          const isRead = readIds.includes(item.id);
          return (
            <Pressable
              key={item.id}
              accessibilityRole="button"
              accessibilityLabel={`Mark ${item.title} as ${isRead ? "unread" : "read"}`}
              onPress={() => toggleRead(item.id)}
              style={({ pressed }) => [
                styles.card,
                isRead && styles.cardRead,
                pressed && styles.pressed,
              ]}
            >
              <View style={[styles.iconWrap, { backgroundColor: tone.tint }]}>
                <Ionicons name={item.icon} size={21} color={tone.color} />
              </View>
              <View style={styles.cardCopy}>
                <View style={styles.titleRow}>
                  <Text style={styles.title}>{item.title}</Text>
                  {!isRead ? <View style={styles.unreadDot} /> : null}
                </View>
                <Text style={styles.bodyText}>{item.body}</Text>
                <Text style={styles.time}>{item.time}</Text>
              </View>
            </Pressable>
          );
        })}

        <View style={styles.note}>
          <Ionicons name="information-circle-outline" size={15} color={colors.greenDeep} />
          <Text style={styles.noteText}>
            Notifications are generated locally from your latest risk signal.
          </Text>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    padding: spacing.lg,
    gap: spacing.md,
  },
  markRead: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.16)",
  },
  pressed: {
    opacity: 0.78,
  },
  markReadText: {
    color: colors.white,
    fontFamily: fonts.medium,
    fontSize: 11,
    lineHeight: 16,
  },
  summaryCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    backgroundColor: colors.greenPale,
    borderRadius: radii.lg,
    padding: spacing.md,
  },
  summaryCopy: {
    flex: 1,
  },
  summaryTitle: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
  },
  summaryText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    marginTop: 2,
  },
  card: {
    flexDirection: "row",
    gap: spacing.md,
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  cardRead: {
    opacity: 0.65,
  },
  iconWrap: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  cardCopy: {
    flex: 1,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
    flex: 1,
  },
  unreadDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: colors.red,
  },
  bodyText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    marginTop: 3,
  },
  time: {
    color: colors.textMuted,
    fontFamily: fonts.medium,
    fontSize: 10,
    lineHeight: 14,
    marginTop: spacing.sm,
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
