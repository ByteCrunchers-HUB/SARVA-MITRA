import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { colors, fonts, shadows } from "@/theme";

function CenterTabButton(props: any) {
  const focused = props.accessibilityState?.selected;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Crop risk prediction"
      onLongPress={props.onLongPress}
      onPress={props.onPress}
      style={styles.centerWrap}
    >
      <View style={[styles.centerButton, focused && styles.centerButtonActive]}>
        <Ionicons name="leaf" size={27} color={colors.white} />
      </View>
    </Pressable>
  );
}

export default function TabsLayout() {
  const insets = useSafeAreaInsets();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.greenDeep,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarHideOnKeyboard: true,
        tabBarLabelStyle: {
          fontFamily: fonts.medium,
          fontSize: 10,
          lineHeight: 14,
        },
        tabBarStyle: {
          height: 62 + insets.bottom,
          paddingTop: 6,
          paddingBottom: Math.max(insets.bottom, 6),
          backgroundColor: colors.card,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          overflow: "visible",
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home-outline" size={size} color={String(color)} />
          ),
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: "History",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="time-outline" size={size} color={String(color)} />
          ),
        }}
      />
      <Tabs.Screen
        name="predict"
        options={{
          title: "",
          tabBarShowLabel: false,
          tabBarButton: (props) => <CenterTabButton {...props} />,
        }}
      />
      <Tabs.Screen
        name="schemes"
        options={{
          title: "Schemes",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="business-outline" size={size} color={String(color)} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person-outline" size={size} color={String(color)} />
          ),
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  centerWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    marginTop: -26,
  },
  centerButton: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: colors.greenDeep,
    borderWidth: 4,
    borderColor: colors.card,
    alignItems: "center",
    justifyContent: "center",
    ...shadows.fab,
  },
  centerButtonActive: {
    backgroundColor: colors.green,
  },
});
