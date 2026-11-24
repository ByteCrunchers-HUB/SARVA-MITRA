import Svg, { Path } from "react-native-svg";

import { colors } from "@/theme";

type LogoProps = {
  size?: number;
  color?: string;
  accent?: string;
};

export function Logo({
  size = 64,
  color = colors.white,
  accent = colors.greenBright,
}: LogoProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
      <Path
        d="M31.5 59V31"
        stroke={color}
        strokeWidth={4}
        strokeLinecap="round"
      />
      <Path
        d="M31.5 37C19 37 10 28 10 13C24 13 33 22 33 37Z"
        fill={color}
      />
      <Path
        d="M33 31C45 31 54 22 54 8C40 8 31 17 31 31Z"
        fill={accent}
      />
      <Path
        d="M18 47C22 45 26 43 31 42"
        stroke={color}
        strokeWidth={3}
        strokeLinecap="round"
        opacity={0.72}
      />
    </Svg>
  );
}
