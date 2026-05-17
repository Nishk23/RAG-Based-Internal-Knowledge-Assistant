import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#f5f7fb",
        brand: "#0f766e",
        accent: "#0ea5e9",
        soft: "#dbeafe"
      },
      boxShadow: {
        panel: "0 18px 40px -24px rgba(15, 23, 42, 0.35)"
      }
    }
  },
  plugins: []
};

export default config;
