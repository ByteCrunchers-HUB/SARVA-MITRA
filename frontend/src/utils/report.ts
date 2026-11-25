import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { Alert, Platform } from "react-native";
import { API_BASE_URL, sendChat } from "@/api/client";
import type { FarmConfig } from "@/api/types";
import { getLatestAdvisoryText, saveLatestAdvisoryText } from "@/store/chat";

export type DownloadAdvisoryReportOptions = {
  farm: FarmConfig;
  advisoryText?: string | null;
  onSuccess?: () => void;
  onError?: (err: Error) => void;
};

/**
 * Cleans assistant response text by removing structured JSON markers, raw JSON codeblocks,
 * and markdown wrappers, matching the web app implementation.
 */
export function cleanAssistantText(text: string): string {
  if (!text) return "";
  let cleaned = text;
  // 1. Remove complete or unclosed BEGIN_STRUCTURED_JSON blocks
  cleaned = cleaned.replace(/BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON/gi, "");
  cleaned = cleaned.replace(/BEGIN_STRUCTURED_JSON[\s\S]*$/gi, "");
  // 2. Remove code blocks containing json
  cleaned = cleaned.replace(/```(?:json)?\s*\{[\s\S]*?\}\s*```/gi, "");
  cleaned = cleaned.replace(/```(?:json)?\s*\{[\s\S]*$/gi, "");
  // 3. Remove dangling raw json with response_mode
  cleaned = cleaned.replace(/\{\s*"response_mode"[\s\S]*$/gi, "");
  // 4. Remove isolated markers
  cleaned = cleaned.replace(/END_STRUCTURED_JSON/gi, "");
  // 5. Unwrap markdown code fence wrapper if present
  cleaned = cleaned.replace(/^```(?:markdown)?\s*\n/i, "").replace(/\n```\s*$/i, "");
  return cleaned.trim();
}

/**
 * Converts an ArrayBuffer to a Base64 string in standard JS/React Native environments.
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Generates and downloads the official Sarva Mitra Agronomic Advisory PDF report.
 * Uses HTTP POST to be 100% compatible with production Render backend and local services.
 * - On Native (Android/iOS): Fetches PDF bytes, writes to device storage, and opens native share/save viewer.
 * - On Web: Triggers standard browser file download via Blob.
 *
 * Implements the EXACT process of the web app:
 * 1. Obtains the comprehensive agronomic assessment from /api/chat with mode='report'.
 * 2. Cleans the markdown response text.
 * 3. Sends the full text to /api/report/pdf to render ReportLab tables and formatted markdown.
 */
export async function downloadAdvisoryReport({
  farm,
  advisoryText,
  onSuccess,
  onError,
}: DownloadAdvisoryReportOptions): Promise<void> {
  let reportText = advisoryText ? cleanAssistantText(advisoryText) : "";

  // 1. If no substantial advisory text was provided, check the cache
  if (!reportText || reportText.length < 200) {
    const cached = await getLatestAdvisoryText(farm.crop, farm.stage);
    if (cached && cached.length >= 200) {
      reportText = cleanAssistantText(cached);
    }
  }

  // 2. If still missing or too short, fetch the initial agronomic report from /api/chat (exact same flow as web app)
  if (!reportText || reportText.length < 200) {
    try {
      const initialQuery = `Provide a complete agronomic status assessment and recommendations for ${farm.crop} (${farm.stage}) based on current field conditions.`;
      const chatResponse = await sendChat({
        question: initialQuery,
        crop: farm.crop,
        lat: farm.lat,
        lon: farm.lon,
        location: farm.location,
        stage: farm.stage,
        chat_history: [],
        mode: "report",
      });

      if (chatResponse?.answer) {
        reportText = cleanAssistantText(chatResponse.answer);
        if (reportText && reportText.length >= 200) {
          await saveLatestAdvisoryText(farm.crop, farm.stage, reportText);
        }
      }
    } catch (chatErr) {
      console.warn("Could not pre-fetch chat agronomic report, continuing with backend defaults:", chatErr);
    }
  }

  const payload: Record<string, unknown> = {
    crop: farm.crop,
    location: farm.location,
    lat: farm.lat,
    lon: farm.lon,
    stage: farm.stage,
  };

  if (reportText && reportText.length >= 200) {
    payload.advisory_text = reportText;
  }

  const url = `${API_BASE_URL}/api/report/pdf`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    if (Platform.OS === "web") {
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `sarva_mitra_${farm.crop.toLowerCase()}_advisory_report.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
      onSuccess?.();
      return;
    }

    // Native Mobile (Android & iOS)
    const arrayBuffer = await response.arrayBuffer();
    const base64Data = arrayBufferToBase64(arrayBuffer);

    const baseDir = FileSystem.documentDirectory ?? FileSystem.cacheDirectory ?? "";
    const filename = `sarva_mitra_${farm.crop.toLowerCase()}_advisory_report.pdf`;
    const targetUri = `${baseDir}${filename}`;

    await FileSystem.writeAsStringAsync(targetUri, base64Data, {
      encoding: FileSystem.EncodingType.Base64,
    });

    const isAvailable = await Sharing.isAvailableAsync();
    if (isAvailable) {
      await Sharing.shareAsync(targetUri, {
        mimeType: "application/pdf",
        dialogTitle: "Sarva Mitra Advisory Report",
        UTI: "com.adobe.pdf",
      });
      onSuccess?.();
    } else {
      Alert.alert(
        "Report Downloaded",
        `Your advisory report was saved to: ${targetUri}`,
        [{ text: "OK" }],
      );
      onSuccess?.();
    }
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    onError?.(error);
    Alert.alert(
      "Download Advisory Report",
      `Could not generate report: ${error.message}`,
      [{ text: "OK" }],
    );
  }
}
