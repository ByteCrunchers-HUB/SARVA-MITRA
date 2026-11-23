import AsyncStorage from "@react-native-async-storage/async-storage";

import type { ChatRole, StructuredAdvisory } from "@/api/types";
import type { UiMessage } from "@/types/chat";
import { createId } from "@/utils/id";

const SESSION_KEY = "sarva.chat.session.v1";
const MESSAGES_KEY_PREFIX = "sarva.chat.messages.v1.";

export function newSessionId(): string {
  return createId("session");
}

function messagesKey(sessionId: string): string {
  return `${MESSAGES_KEY_PREFIX}${sessionId}`;
}

export async function getSessionId(): Promise<string> {
  try {
    const existing = await AsyncStorage.getItem(SESSION_KEY);
    if (existing) return existing;
  } catch {
    // fall through to a new session
  }
  const created = newSessionId();
  try {
    await AsyncStorage.setItem(SESSION_KEY, created);
  } catch {
    // keep using the in-memory id
  }
  return created;
}

export async function saveSessionId(sessionId: string): Promise<void> {
  await AsyncStorage.setItem(SESSION_KEY, sessionId);
}

export async function resetSessionId(): Promise<string> {
  const created = newSessionId();
  await saveSessionId(created);
  return created;
}

export async function loadMessages(sessionId: string): Promise<UiMessage[]> {
  try {
    const raw = await AsyncStorage.getItem(messagesKey(sessionId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as UiMessage[];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (message): message is UiMessage =>
        message &&
        typeof message.id === "string" &&
        typeof message.content === "string" &&
        (message.role === "user" ||
          message.role === "assistant" ||
          message.role === "system"),
    );
  } catch {
    return [];
  }
}

export async function saveMessages(
  sessionId: string,
  messages: UiMessage[],
): Promise<void> {
  try {
    await AsyncStorage.setItem(messagesKey(sessionId), JSON.stringify(messages));
  } catch {
    // persistence failure should not break the chat
  }
}

export type StoredMessageShape = {
  role: ChatRole;
  content: string;
  structured?: StructuredAdvisory | null;
};
