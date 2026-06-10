import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#E5192A",
          dark: "#C01020",
          light: "#FF3040",
          foreground: "#FAFAFA",
        },
        background: {
          DEFAULT: "#0A0A0A",
          card: "#111111",
          muted: "#1A1A1A",
        },
        border: {
          DEFAULT: "#222222",
        },
        foreground: {
          DEFAULT: "#FAFAFA",
          muted: "#888888",
        },
        accent: {
          DEFAULT: "#FF3040",
          foreground: "#FAFAFA",
        },
        destructive: {
          DEFAULT: "#E5192A",
          foreground: "#FAFAFA",
        },
        muted: {
          DEFAULT: "#1A1A1A",
          foreground: "#888888",
        },
        card: {
          DEFAULT: "#111111",
          foreground: "#FAFAFA",
        },
        popover: {
          DEFAULT: "#111111",
          foreground: "#FAFAFA",
        },
        secondary: {
          DEFAULT: "#1A1A1A",
          foreground: "#FAFAFA",
        },
        input: "#222222",
        ring: "#E5192A",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "pulse-red": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(229, 25, 42, 0)" },
          "50%": { boxShadow: "0 0 20px 4px rgba(229, 25, 42, 0.4)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        shimmer: "shimmer 2s linear infinite",
        "pulse-red": "pulse-red 2s ease-in-out infinite",
        float: "float 3s ease-in-out infinite",
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        shimmer: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
