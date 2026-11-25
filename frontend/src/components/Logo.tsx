import { Image, ImageStyle, StyleProp } from "react-native";

import { colors } from "@/theme";

type LogoProps = {
  size?: number;
  color?: string;
  accent?: string;
  style?: StyleProp<ImageStyle>;
};

export function Logo({
  size = 64,
  style,
}: LogoProps) {
  return (
    <Image
      source={require("../../assets/logo-compact.png")}
      style={[
        {
          width: size,
          height: size,
          borderRadius: Math.round(size * 0.22),
        },
        style,
      ]}
      resizeMode="cover"
    />
  );
}
