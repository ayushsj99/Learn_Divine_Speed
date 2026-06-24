import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0b0d12",
        surface: "#13161d",
        accent: "#6ee7b7",
      },
    },
  },
  plugins: [],
};

export default config;
