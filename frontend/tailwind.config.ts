import type { Config } from "tailwindcss";

// Design tokens for AI Interview Prep Agent.
// Palette: a quiet "study room before an interview" mood — deep ink-navy
// surfaces, one deliberate amber accent (used only for progress + primary
// actions), and a distinct sage/terracotta pair for gap-addressed vs
// gap-open states. Deliberately not the cream+terracotta or near-black+neon
// defaults.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#0F1420", // page background
          800: "#171D2B", // surface / cards
          700: "#1F2738", // inputs / elevated surface
          600: "#2A3344", // hairline borders
        },
        paper: {
          100: "#EDEFF3", // primary text
          300: "#9AA3B5", // secondary text
        },
        amber: {
          DEFAULT: "#D9A441", // single accent: progress + primary CTA only
          dim: "#B8863A",
        },
        sage: {
          DEFAULT: "#5FB88B", // gap addressed / success
        },
        clay: {
          DEFAULT: "#E0895A", // gap still open / attention
        },
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-plex-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
      },
      maxWidth: {
        prose: "42rem",
      },
      keyframes: {
        "cross-fade": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "cross-fade": "cross-fade 320ms ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
