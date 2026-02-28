/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                // CampusShield brand palette — deep navy + electric teal + alert red
                brand: {
                    50: "#e8f4ff",
                    100: "#c5e2ff",
                    200: "#9acbff",
                    300: "#5daef8",
                    400: "#2990ef",
                    500: "#0970d4",
                    600: "#0558a8",
                    700: "#044085",
                    800: "#022c66",
                    900: "#011a42",
                    950: "#000d24",
                },
                teal: {
                    400: "#22d3ee",
                    500: "#06b6d4",
                    600: "#0891b2",
                },
                risk: {
                    low: "#22c55e",  // green
                    medium: "#f59e0b",  // amber
                    high: "#ef4444",  // red
                    critical: "#7c3aed", // purple
                },
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
            backgroundImage: {
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
                "brand-gradient": "linear-gradient(135deg, #011a42 0%, #022c66 50%, #044085 100%)",
                "glow-teal": "radial-gradient(ellipse at 50% 50%, rgba(6,182,212,0.15) 0%, transparent 70%)",
            },
            boxShadow: {
                "glow-teal": "0 0 24px rgba(6,182,212,0.4)",
                "glow-red": "0 0 24px rgba(239,68,68,0.4)",
                "card": "0 4px 24px rgba(0,0,0,0.3)",
            },
            animation: {
                "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                "slide-up": "slideUp 0.3s ease-out",
                "fade-in": "fadeIn 0.4s ease-out",
            },
            keyframes: {
                slideUp: {
                    "0%": { transform: "translateY(20px)", opacity: "0" },
                    "100%": { transform: "translateY(0)", opacity: "1" },
                },
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
            },
        },
    },
    plugins: [],
};
