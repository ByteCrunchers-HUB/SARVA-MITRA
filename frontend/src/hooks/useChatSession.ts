import { useCallback, useEffect, useRef, useState } from "react";

import { sendChat } from "@/api/client";
import type { ChatHistoryMessage } from "@/api/types";
import { useFarmConfig } from "@/hooks/useFarmConfig";
import {
  getSessionId,
  loadMessages,
  saveMessages,
  saveSessionId,
} from "@/store/chat";
import type { UiMessage } from "@/types/chat";
import { createId } from "@/utils/id";

export function useChatSession() {
  const { farm } = useFarmConfig();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const didInitialDiagnosis = useRef(false);

  useEffect(() => {
    let active = true;
    (async () => {
      const storedSession = await getSessionId();
      const storedMessages = await loadMessages(storedSession);
      if (!active) return;
      setSessionId(storedSession);
      setMessages(storedMessages);
      setInitialized(true);
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!initialized || !sessionId) return;
    void saveMessages(sessionId, messages);
  }, [initialized, messages, sessionId]);

  const send = useCallback(
    async (question: string, options?: { replaceLastUser?: boolean }) => {
      const trimmed = question.trim();
      if (!trimmed || isSending) return;

      setLastQuestion(trimmed);
      setError(null);
      setIsSending(true);

      const userMessage: UiMessage = {
        id: createId("msg"),
        role: "user",
        content: trimmed,
        createdAt: new Date().toISOString(),
      };

      const baseMessages = options?.replaceLastUser
        ? messages.slice(0, -1)
        : messages;
      const history: ChatHistoryMessage[] = baseMessages.map((message) => ({
        role: message.role,
        content: message.content,
      }));

      setMessages([...baseMessages, userMessage]);

      try {
        const response = await sendChat({
          question: trimmed,
          crop: farm.crop,
          lat: farm.lat,
          lon: farm.lon,
          location: farm.location,
          chat_history: history,
          session_id: sessionId ?? undefined,
        });

        const assistantMessage: UiMessage = {
          id: createId("msg"),
          role: "assistant",
          content: response.answer,
          createdAt: new Date().toISOString(),
          structured: response.structured,
        };
        setMessages((current) => [...current, assistantMessage]);

        if (response.session_id && response.session_id !== sessionId) {
          await saveSessionId(response.session_id);
          setSessionId(response.session_id);
        }
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "Could not reach the AI assistant.",
        );
      } finally {
        setIsSending(false);
      }
    },
    [farm, isSending, messages, sessionId],
  );

  useEffect(() => {
    if (!initialized || didInitialDiagnosis.current || messages.length > 0) {
      return;
    }
    didInitialDiagnosis.current = true;
    void send(
      `Give me a proactive crop health diagnosis for my ${farm.crop} crop at ${farm.location} using today’s weather and soil reference.`,
    );
  }, [farm.crop, farm.location, initialized, messages.length, send]);

  const retry = useCallback(() => {
    if (lastQuestion) void send(lastQuestion, { replaceLastUser: true });
  }, [lastQuestion, send]);

  const reset = useCallback(async () => {
    didInitialDiagnosis.current = false;
    const freshSession = createId("session");
    await saveSessionId(freshSession);
    await saveMessages(freshSession, []);
    setSessionId(freshSession);
    setMessages([]);
    setError(null);
    setLastQuestion(null);
  }, []);

  return {
    messages,
    send,
    retry,
    reset,
    isSending,
    error,
    initialized,
    sessionId,
  };
}
