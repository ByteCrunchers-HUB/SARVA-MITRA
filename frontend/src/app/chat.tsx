import { Ionicons } from "@expo/vector-icons";
import { useEffect, useRef, useState } from "react";
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
  type ScrollViewInstance,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { GreenHeader } from "@/components/GreenHeader";
import { IconButton } from "@/components/IconButton";
import { useChatSession } from "@/hooks/useChatSession";
import { useFarmConfig } from "@/hooks/useFarmConfig";
import { colors, fonts, radii, sizes, spacing } from "@/theme";
import type { UiMessage } from "@/types/chat";

const QUICK_QUESTIONS = [
  "Is blight likely tomorrow?",
  "Irrigation advice for my crop",
  "Fertilizer suggestion",
];

function formatTime(iso: string): string {
  return iso.length >= 16 ? iso.slice(11, 16) : "";
}

function MessageBubble({ message }: { message: UiMessage }) {
  const isUser = message.role === "user";
  const recommendations = Array.isArray(message.structured?.recommendations)
    ? message.structured.recommendations
        .filter((item): item is string => typeof item === "string")
        .slice(0, 3)
    : [];

  return (
    <View style={[styles.messageRow, isUser && styles.messageRowUser]}>
      {!isUser ? (
        <View style={styles.assistantAvatar}>
          <Ionicons name="leaf" size={15} color={colors.white} />
        </View>
      ) : null}
      <View style={[styles.bubble, isUser && styles.bubbleUser]}>
        <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>
          {message.content}
        </Text>
        {recommendations.length > 0 ? (
          <View style={styles.recommendations}>
            <Text style={styles.recommendationsTitle}>Key actions</Text>
            {recommendations.map((item) => (
              <View key={item} style={styles.recommendationRow}>
                <Ionicons name="checkmark" size={13} color={colors.green} />
                <Text style={styles.recommendationText}>{item}</Text>
              </View>
            ))}
          </View>
        ) : null}
        <Text style={[styles.time, isUser && styles.timeUser]}>
          {formatTime(message.createdAt)}
        </Text>
      </View>
    </View>
  );
}

export default function ChatScreen() {
  const { farm } = useFarmConfig();
  const {
    messages,
    send,
    retry,
    reset,
    isSending,
    error,
    initialized,
  } = useChatSession();
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<ScrollViewInstance>(null);

  useEffect(() => {
    const timer = setTimeout(
      () => scrollRef.current?.scrollToEnd({ animated: true }),
      80,
    );
    return () => clearTimeout(timer);
  }, [messages.length, isSending, error]);

  const handleSend = () => {
    const question = draft.trim();
    if (!question || isSending) return;
    setDraft("");
    void send(question);
  };

  const handleReset = () => {
    Alert.alert(
      "Start a new chat?",
      "This clears the conversation on this device.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "New Chat",
          style: "destructive",
          onPress: () => void reset(),
        },
      ],
    );
  };

  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.root}>
      <GreenHeader
        showBack
        title="AI Assistant"
        subtitle={`${farm.crop} · ${farm.location}`}
        right={
          <IconButton
            accessibilityLabel="Start a new chat"
            name="refresh-outline"
            onPress={handleReset}
          />
        }
      />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          ref={scrollRef}
          style={styles.messages}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {!initialized ? (
            <View style={styles.centerState}>
              <ActivityIndicator size="small" color={colors.greenDeep} />
              <Text style={styles.centerText}>Loading conversation...</Text>
            </View>
          ) : null}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {isSending ? (
            <View style={styles.messageRow}>
              <View style={styles.assistantAvatar}>
                <Ionicons name="leaf" size={15} color={colors.white} />
              </View>
              <View style={[styles.bubble, styles.typingBubble]}>
                <ActivityIndicator size="small" color={colors.greenDeep} />
                <Text style={styles.typingText}>Thinking...</Text>
              </View>
            </View>
          ) : null}

          {error ? (
            <View style={styles.errorBox}>
              <Ionicons
                name="warning-outline"
                size={18}
                color={colors.amberDark}
              />
              <Text style={styles.errorText}>{error}</Text>
              <Pressable onPress={retry} accessibilityRole="button">
                <Text style={styles.retryText}>Retry</Text>
              </Pressable>
            </View>
          ) : null}
        </ScrollView>

        <View style={styles.composer}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.quickRow}
            contentContainerStyle={styles.quickContent}
          >
            {QUICK_QUESTIONS.map((question) => (
              <Pressable
                key={question}
                accessibilityRole="button"
                accessibilityLabel={question}
                onPress={() => {
                  if (!isSending) void send(question);
                }}
                style={styles.chip}
              >
                <Text style={styles.chipText}>{question}</Text>
              </Pressable>
            ))}
          </ScrollView>

          <View style={styles.inputRow}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Attach a photo"
              onPress={() =>
                Alert.alert(
                  "Photo attachments coming soon.",
                  "For now, describe what you see in the field.",
                )
              }
              style={styles.attachButton}
            >
              <Ionicons name="attach-outline" size={21} color={colors.textMuted} />
            </Pressable>
            <TextInput
              value={draft}
              onChangeText={setDraft}
              placeholder="Ask about soil, crops or weather..."
              placeholderTextColor={colors.textMuted}
              multiline
              style={styles.input}
            />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Send message"
              disabled={!draft.trim() || isSending}
              onPress={handleSend}
              style={({ pressed }) => [
                styles.sendButton,
                (!draft.trim() || isSending) && styles.sendDisabled,
                pressed && draft.trim() && styles.sendPressed,
              ]}
            >
              <Ionicons name="arrow-up" size={20} color={colors.white} />
            </Pressable>
          </View>

          <Text style={styles.disclaimer}>
            Advisory support only · confirm with a local expert before spraying
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.page,
  },
  flex: {
    flex: 1,
  },
  messages: {
    flex: 1,
  },
  messagesContent: {
    padding: spacing.lg,
    paddingBottom: spacing.md,
    gap: spacing.md,
  },
  centerState: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    padding: spacing.xl,
  },
  centerText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  messageRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: spacing.sm,
    maxWidth: "88%",
  },
  messageRowUser: {
    alignSelf: "flex-end",
  },
  assistantAvatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.greenDeep,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  bubble: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderBottomLeftRadius: 6,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    flexShrink: 1,
  },
  bubbleUser: {
    backgroundColor: colors.greenDeep,
    borderColor: colors.greenDeep,
    borderBottomLeftRadius: radii.lg,
    borderBottomRightRadius: 6,
  },
  bubbleText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
  },
  bubbleTextUser: {
    color: colors.white,
  },
  recommendations: {
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  recommendationsTitle: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: 10,
    lineHeight: 14,
    marginBottom: 4,
  },
  recommendationRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 5,
    marginBottom: 3,
  },
  recommendationText: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: 11,
    lineHeight: 16,
    flex: 1,
  },
  time: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 9,
    lineHeight: 12,
    textAlign: "right",
    marginTop: 4,
  },
  timeUser: {
    color: colors.white70,
  },
  typingBubble: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  typingText: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.amberSoft,
    borderRadius: radii.md,
    padding: spacing.md,
  },
  errorText: {
    color: colors.amberDark,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 19,
    flex: 1,
  },
  retryText: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  composer: {
    backgroundColor: colors.card,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
  },
  quickRow: {
    marginBottom: spacing.sm,
  },
  quickContent: {
    gap: spacing.sm,
    paddingRight: spacing.sm,
  },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 7,
    borderRadius: 999,
    backgroundColor: colors.greenPale,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipText: {
    color: colors.greenDeep,
    fontFamily: fonts.medium,
    fontSize: 11,
    lineHeight: 16,
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: spacing.sm,
  },
  attachButton: {
    width: 40,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 110,
    backgroundColor: colors.page,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingTop: 11,
    paddingBottom: 11,
    color: colors.text,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.greenDeep,
    alignItems: "center",
    justifyContent: "center",
  },
  sendDisabled: {
    backgroundColor: colors.border,
  },
  sendPressed: {
    opacity: 0.85,
  },
  disclaimer: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 9,
    lineHeight: 13,
    textAlign: "center",
    marginTop: spacing.sm,
  },
});
