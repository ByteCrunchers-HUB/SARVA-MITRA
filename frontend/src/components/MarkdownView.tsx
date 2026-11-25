import { ReactNode } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TextStyle,
  View,
  ViewStyle,
} from "react-native";
import { colors, fonts, radii, sizes, spacing } from "@/theme";

type MarkdownViewProps = {
  content: string;
  isUser?: boolean;
  style?: ViewStyle;
  baseTextStyle?: TextStyle;
};

/**
 * Parses inline formatting:
 * - Bold: **text** or __text__
 * - Italic: *text* or _text_
 * - Bold-Italic: ***text***
 * - Inline Code: `code`
 * - Links: [label](url)
 */
function renderInline(
  text: string,
  baseStyle: TextStyle,
  isUser: boolean,
): ReactNode[] {
  // Regex to match markdown inline tokens
  const tokenRegex =
    /(\*\*\*[\s\S]+?\*\*\*|\*\*[\s\S]+?\*\*|___[\s\S]+?___|__[\s\S]+?__|(?<!\*)\*(?!\*)[\s\S]+?(?<!\*)\*(?!\*)|`[^`\n]+`|\[[^\]]+\]\([^)]+\))/g;

  const parts = text.split(tokenRegex);

  return parts.map((part, index) => {
    if (!part) return null;

    // Bold + Italic: ***text*** or ___text___
    if (
      (part.startsWith("***") && part.endsWith("***") && part.length >= 6) ||
      (part.startsWith("___") && part.endsWith("___") && part.length >= 6)
    ) {
      const inner = part.slice(3, -3);
      return (
        <Text
          key={index}
          style={[
            baseStyle,
            {
              fontFamily: fonts.bold,
              fontWeight: "700",
              fontStyle: "italic",
              color: isUser ? colors.white : colors.text,
            },
          ]}
        >
          {inner}
        </Text>
      );
    }

    // Bold: **text** or __text__
    if (
      (part.startsWith("**") && part.endsWith("**") && part.length >= 4) ||
      (part.startsWith("__") && part.endsWith("__") && part.length >= 4)
    ) {
      const inner = part.slice(2, -2);
      return (
        <Text
          key={index}
          style={[
            baseStyle,
            {
              fontFamily: fonts.bold,
              fontWeight: "700",
              color: isUser ? colors.white : colors.text,
            },
          ]}
        >
          {inner}
        </Text>
      );
    }

    // Italic: *text*
    if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
      const inner = part.slice(1, -1);
      return (
        <Text key={index} style={[baseStyle, { fontStyle: "italic" }]}>
          {inner}
        </Text>
      );
    }

    // Inline Code: `code`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      const inner = part.slice(1, -1);
      return (
        <Text
          key={index}
          style={[
            baseStyle,
            {
              fontFamily: "monospace",
              fontSize: (baseStyle.fontSize ?? sizes.small) * 0.92,
              backgroundColor: isUser
                ? "rgba(255, 255, 255, 0.22)"
                : "#EAEFEA",
              color: isUser ? colors.white : colors.greenDeep,
              borderRadius: 4,
              paddingHorizontal: 4,
            },
          ]}
        >
          {inner}
        </Text>
      );
    }

    // Markdown link: [label](url) -> display label
    if (part.startsWith("[") && part.includes("](") && part.endsWith(")")) {
      const match = part.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (match) {
        return (
          <Text
            key={index}
            style={[
              baseStyle,
              {
                color: isUser ? colors.white : colors.greenDeep,
                textDecorationLine: "underline",
                fontFamily: fonts.semibold,
              },
            ]}
          >
            {match[1]}
          </Text>
        );
      }
    }

    // Regular text
    return (
      <Text key={index} style={baseStyle}>
        {part}
      </Text>
    );
  });
}

function isTableRow(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) return false;
  if (
    trimmed.startsWith("|") &&
    (trimmed.endsWith("|") || trimmed.split("|").length >= 2)
  ) {
    return true;
  }
  if (trimmed.split("|").length >= 3) {
    return true;
  }
  if (/^:?-+:?(\|:?-+:?)+$/.test(trimmed)) {
    return true;
  }
  return false;
}

function parseTableCells(line: string): string[] {
  let trimmed = line.trim();
  if (trimmed.startsWith("|")) trimmed = trimmed.slice(1);
  if (trimmed.endsWith("|")) trimmed = trimmed.slice(0, -1);
  return trimmed.split("|").map((cell) => cell.trim());
}

function isTableDelimiter(line: string): boolean {
  const cells = parseTableCells(line);
  return (
    cells.length > 0 &&
    cells.every((cell) => /^:?-+:?$/.test(cell.trim()) || cell.trim() === "")
  );
}

function padRow(cells: string[], count: number): string[] {
  const r = [...cells];
  while (r.length < count) r.push("");
  return r;
}

/**
 * Rich Markdown renderer for React Native chat bubbles & advisory cards.
 * Formats Headings, Tables, Bullet Lists, Numbered Lists, Code blocks, and bold/italic elements.
 */
export function MarkdownView({
  content,
  isUser = false,
  style,
  baseTextStyle,
}: MarkdownViewProps) {
  if (!content) return null;

  const effectiveBaseStyle: TextStyle = StyleSheet.flatten([
    styles.defaultText,
    isUser ? styles.userText : styles.assistantText,
    baseTextStyle,
  ]) || styles.defaultText;

  // Split lines
  const lines = content.split(/\r?\n/);
  const elements: ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockBuffer: string[] = [];
  let tableBuffer: string[] = [];

  const flushTable = (keyPrefix: string | number) => {
    if (tableBuffer.length === 0) return;

    const rawLines = [...tableBuffer];
    tableBuffer = [];

    let headerRow: string[] = [];
    const bodyRows: string[][] = [];

    for (let i = 0; i < rawLines.length; i++) {
      const rawLine = rawLines[i];
      if (i === 1 && isTableDelimiter(rawLine)) {
        continue;
      }
      const cells = parseTableCells(rawLine);
      if (i === 0) {
        headerRow = cells;
      } else {
        bodyRows.push(cells);
      }
    }

    // Determine max columns
    const allRows = headerRow.length > 0 ? [headerRow, ...bodyRows] : bodyRows;
    const colCount = Math.max(...allRows.map((r) => r.length), 1);

    const normalizedHeader =
      headerRow.length > 0 ? padRow(headerRow, colCount) : null;
    const normalizedBody = bodyRows.map((r) => padRow(r, colCount));

    elements.push(
      <ScrollView
        key={`tbl-scroll-${keyPrefix}`}
        horizontal
        showsHorizontalScrollIndicator={true}
        style={styles.tableScroll}
        contentContainerStyle={styles.tableScrollContent}
      >
        <View
          style={[styles.tableContainer, isUser && styles.tableContainerUser]}
        >
          {normalizedHeader && (
            <View
              style={[
                styles.tableRow,
                styles.tableHeaderRow,
                isUser && styles.tableHeaderRowUser,
              ]}
            >
              {normalizedHeader.map((headerCell, cIdx) => (
                <View
                  key={`th-${cIdx}`}
                  style={[
                    styles.tableCell,
                    styles.tableHeaderCell,
                    cIdx === colCount - 1 && styles.tableCellLastCol,
                  ]}
                >
                  <Text
                    style={[
                      styles.tableHeaderText,
                      isUser && styles.tableTextUser,
                    ]}
                  >
                    {renderInline(headerCell, styles.tableHeaderText, isUser)}
                  </Text>
                </View>
              ))}
            </View>
          )}

          {normalizedBody.map((row, rIdx) => (
            <View
              key={`tr-${rIdx}`}
              style={[
                styles.tableRow,
                rIdx % 2 === 1 &&
                  (isUser ? styles.tableRowAltUser : styles.tableRowAlt),
                rIdx === normalizedBody.length - 1 && styles.tableRowLast,
              ]}
            >
              {row.map((cell, cIdx) => (
                <View
                  key={`td-${cIdx}`}
                  style={[
                    styles.tableCell,
                    cIdx === colCount - 1 && styles.tableCellLastCol,
                  ]}
                >
                  <Text
                    style={[
                      styles.tableCellText,
                      isUser && styles.tableTextUser,
                    ]}
                  >
                    {renderInline(cell, styles.tableCellText, isUser)}
                  </Text>
                </View>
              ))}
            </View>
          ))}
        </View>
      </ScrollView>,
    );
  };

  lines.forEach((line, lineIndex) => {
    const trimmed = line.trim();

    // Check for code block fence
    if (trimmed.startsWith("```")) {
      flushTable(`code-${lineIndex}`);
      if (inCodeBlock) {
        // End code block
        elements.push(
          <View
            key={`code-${lineIndex}`}
            style={[
              styles.codeBlock,
              isUser && { backgroundColor: "rgba(0,0,0,0.18)" },
            ]}
          >
            <Text
              style={[
                styles.codeText,
                isUser && { color: colors.white },
              ]}
            >
              {codeBlockBuffer.join("\n")}
            </Text>
          </View>,
        );
        codeBlockBuffer = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockBuffer.push(line);
      return;
    }

    // Check for table row
    if (isTableRow(trimmed)) {
      tableBuffer.push(trimmed);
      return;
    }

    // Flush any pending table before regular markdown elements
    flushTable(`line-${lineIndex}`);

    // Empty lines act as separators
    if (!trimmed) {
      elements.push(<View key={`spacer-${lineIndex}`} style={styles.spacer} />);
      return;
    }

    // Headings
    if (trimmed.startsWith("#### ")) {
      const text = trimmed.slice(5);
      elements.push(
        <Text
          key={`h4-${lineIndex}`}
          style={[
            effectiveBaseStyle,
            styles.h4,
            isUser && { color: colors.white },
          ]}
        >
          {renderInline(text, effectiveBaseStyle, isUser)}
        </Text>,
      );
      return;
    }

    if (trimmed.startsWith("### ")) {
      const text = trimmed.slice(4);
      elements.push(
        <Text
          key={`h3-${lineIndex}`}
          style={[
            effectiveBaseStyle,
            styles.h3,
            isUser && { color: colors.white },
          ]}
        >
          {renderInline(text, effectiveBaseStyle, isUser)}
        </Text>,
      );
      return;
    }

    if (trimmed.startsWith("## ")) {
      const text = trimmed.slice(3);
      elements.push(
        <Text
          key={`h2-${lineIndex}`}
          style={[
            effectiveBaseStyle,
            styles.h2,
            isUser && { color: colors.white },
          ]}
        >
          {renderInline(text, effectiveBaseStyle, isUser)}
        </Text>,
      );
      return;
    }

    if (trimmed.startsWith("# ")) {
      const text = trimmed.slice(2);
      elements.push(
        <Text
          key={`h1-${lineIndex}`}
          style={[
            effectiveBaseStyle,
            styles.h1,
            isUser && { color: colors.white },
          ]}
        >
          {renderInline(text, effectiveBaseStyle, isUser)}
        </Text>,
      );
      return;
    }

    // Horizontal Rule
    if (/^[-*_]{3,}$/.test(trimmed)) {
      elements.push(
        <View
          key={`hr-${lineIndex}`}
          style={[
            styles.hr,
            isUser && { backgroundColor: "rgba(255,255,255,0.3)" },
          ]}
        />,
      );
      return;
    }

    // Blockquote: > text
    if (trimmed.startsWith("> ")) {
      const text = trimmed.slice(2);
      elements.push(
        <View
          key={`quote-${lineIndex}`}
          style={[
            styles.blockquote,
            isUser && {
              borderLeftColor: colors.white,
              backgroundColor: "rgba(255,255,255,0.12)",
            },
          ]}
        >
          <Text style={effectiveBaseStyle}>
            {renderInline(text, effectiveBaseStyle, isUser)}
          </Text>
        </View>,
      );
      return;
    }

    // Unordered List Items: •, -, *, +
    const bulletMatch = trimmed.match(/^([•\-\*\+])\s+(.+)$/);
    if (bulletMatch) {
      const text = bulletMatch[2];
      elements.push(
        <View key={`bullet-${lineIndex}`} style={styles.listRow}>
          <Text
            style={[
              styles.bulletSymbol,
              isUser ? { color: colors.white } : { color: colors.greenDeep },
            ]}
          >
            •
          </Text>
          <Text style={[styles.listContent, effectiveBaseStyle]}>
            {renderInline(text, effectiveBaseStyle, isUser)}
          </Text>
        </View>,
      );
      return;
    }

    // Numbered List Items: 1., 2., etc.
    const numberMatch = trimmed.match(/^(\d+[\.\)])\s+(.+)$/);
    if (numberMatch) {
      const numLabel = numberMatch[1];
      const text = numberMatch[2];
      elements.push(
        <View key={`num-${lineIndex}`} style={styles.listRow}>
          <Text
            style={[
              styles.numLabel,
              isUser ? { color: colors.white } : { color: colors.greenDeep },
            ]}
          >
            {numLabel}
          </Text>
          <Text style={[styles.listContent, effectiveBaseStyle]}>
            {renderInline(text, effectiveBaseStyle, isUser)}
          </Text>
        </View>,
      );
      return;
    }

    // Regular paragraph line
    elements.push(
      <Text key={`line-${lineIndex}`} style={[effectiveBaseStyle, styles.paragraph]}>
        {renderInline(trimmed, effectiveBaseStyle, isUser)}
      </Text>,
    );
  });

  // Flush any trailing table
  flushTable("end");

  // If a code block was not closed
  if (inCodeBlock && codeBlockBuffer.length > 0) {
    elements.push(
      <View
        key="code-unclosed"
        style={[
          styles.codeBlock,
          isUser && { backgroundColor: "rgba(0,0,0,0.18)" },
        ]}
      >
        <Text
          style={[
            styles.codeText,
            isUser && { color: colors.white },
          ]}
        >
          {codeBlockBuffer.join("\n")}
        </Text>
      </View>,
    );
  }

  return <View style={style}>{elements}</View>;
}

const styles = StyleSheet.create({
  defaultText: {
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 21,
  },
  assistantText: {
    color: colors.textBody,
  },
  userText: {
    color: colors.white,
  },
  paragraph: {
    marginBottom: 4,
  },
  spacer: {
    height: 6,
  },
  h1: {
    fontFamily: fonts.bold,
    fontSize: sizes.h2,
    lineHeight: 26,
    color: colors.text,
    marginTop: spacing.sm,
    marginBottom: 4,
  },
  h2: {
    fontFamily: fonts.bold,
    fontSize: sizes.h3,
    lineHeight: 24,
    color: colors.text,
    marginTop: spacing.sm,
    marginBottom: 4,
  },
  h3: {
    fontFamily: fonts.semibold,
    fontSize: sizes.body,
    lineHeight: 22,
    color: colors.greenDeep,
    marginTop: 6,
    marginBottom: 4,
  },
  h4: {
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 20,
    color: colors.greenDeep,
    marginTop: 4,
    marginBottom: 2,
  },
  listRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 4,
    paddingLeft: 2,
  },
  bulletSymbol: {
    fontSize: 16,
    lineHeight: 20,
    marginRight: 7,
    fontWeight: "700",
  },
  numLabel: {
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 21,
    marginRight: 6,
  },
  listContent: {
    flex: 1,
    lineHeight: 21,
  },
  blockquote: {
    borderLeftWidth: 3,
    borderLeftColor: colors.greenDeep,
    backgroundColor: "#F2F7F2",
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: radii.sm,
    marginVertical: 4,
  },
  hr: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: colors.border,
    marginVertical: spacing.sm,
  },
  codeBlock: {
    backgroundColor: "#243228",
    padding: spacing.sm,
    borderRadius: radii.sm,
    marginVertical: 4,
  },
  codeText: {
    color: "#E2F0D9",
    fontFamily: "monospace",
    fontSize: 12,
    lineHeight: 18,
  },
  tableScroll: {
    marginVertical: 8,
    borderRadius: 8,
  },
  tableScrollContent: {
    paddingVertical: 2,
  },
  tableContainer: {
    borderWidth: 1,
    borderColor: "#D0DEC9",
    borderRadius: 8,
    overflow: "hidden",
    backgroundColor: colors.white,
  },
  tableContainerUser: {
    borderColor: "rgba(255,255,255,0.35)",
    backgroundColor: "rgba(0,0,0,0.12)",
  },
  tableRow: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "#E4EDE2",
  },
  tableRowLast: {
    borderBottomWidth: 0,
  },
  tableHeaderRow: {
    backgroundColor: "#EBF3E8",
    borderBottomWidth: 1.5,
    borderBottomColor: "#C3D6BA",
  },
  tableHeaderRowUser: {
    backgroundColor: "rgba(255,255,255,0.18)",
    borderBottomColor: "rgba(255,255,255,0.35)",
  },
  tableRowAlt: {
    backgroundColor: "#F7FAF6",
  },
  tableRowAltUser: {
    backgroundColor: "rgba(255,255,255,0.06)",
  },
  tableCell: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    minWidth: 95,
    maxWidth: 240,
    borderRightWidth: 1,
    borderRightColor: "#E4EDE2",
    justifyContent: "center",
  },
  tableHeaderCell: {
    borderRightColor: "#C3D6BA",
  },
  tableCellLastCol: {
    borderRightWidth: 0,
  },
  tableHeaderText: {
    fontFamily: fonts.bold,
    fontSize: sizes.small,
    color: colors.greenDeep,
    lineHeight: 18,
    fontWeight: "700",
  },
  tableCellText: {
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    color: colors.textBody,
    lineHeight: 18,
  },
  tableTextUser: {
    color: colors.white,
  },
});
