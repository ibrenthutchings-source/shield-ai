import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        difesa: {
          forest: "#003A12",
          leaf: "#4A5949",
          grey: "#546E7A",
          cream: "#F1F8E9",
          ochre: "#A68C52",
        },
      },
    },
  },
  plugins: [],
};

export default config;
