import type { ChatRole, StructuredAdvisory } from "@/api/types";

export type UiMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  structured?: StructuredAdvisory | null;
  isInitialReport?: boolean;
};
