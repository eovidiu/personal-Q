/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
    "./main.tsx",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    "container": {
        "center": true,
        "screens": {
            "2xl": "1400px"
        }
    },
    "extend": {
        "fontFamily": {
            "sans": [
                "var(--font-sans)",
                "ui-sans-serif",
                "system-ui",
                "-apple-system",
                "BlinkMacSystemFont",
                "\"Segoe UI\"",
                "Roboto",
                "\"Helvetica Neue\"",
                "Arial",
                "\"Noto Sans\"",
                "sans-serif",
                "\"Apple Color Emoji\"",
                "\"Segoe UI Emoji\"",
                "\"Segoe UI Symbol\"",
                "\"Noto Color Emoji\""
            ],
            "serif": [
                "var(--font-serif)",
                "ui-serif",
                "Georgia",
                "Cambria",
                "\"Times New Roman\"",
                "Times",
                "serif"
            ],
            "mono": [
                "var(--font-mono)",
                "ui-monospace",
                "SFMono-Regular",
                "Menlo",
                "Monaco",
                "Consolas",
                "\"Liberation Mono\"",
                "\"Courier New\"",
                "monospace"
            ]
        },
        "colors": {
            "border": "hsl(var(--border))",
            "input": "hsl(var(--input))",
            "ring": "hsl(var(--ring))",
            "background": "hsl(var(--background))",
            "foreground": "hsl(var(--foreground))",
            "primary": {
                "DEFAULT": "hsl(var(--primary))",
                "foreground": "hsl(var(--primary-foreground))"
            },
            "secondary": {
                "DEFAULT": "hsl(var(--secondary))",
                "foreground": "hsl(var(--secondary-foreground))"
            },
            "destructive": {
                "DEFAULT": "hsl(var(--destructive))",
                "foreground": "hsl(var(--destructive-foreground))"
            },
            "muted": {
                "DEFAULT": "hsl(var(--muted))",
                "foreground": "hsl(var(--muted-foreground))"
            },
            "accent": {
                "DEFAULT": "hsl(var(--accent))",
                "foreground": "hsl(var(--accent-foreground))"
            },
            "popover": {
                "DEFAULT": "hsl(var(--popover))",
                "foreground": "hsl(var(--popover-foreground))"
            },
            "card": {
                "DEFAULT": "hsl(var(--card))",
                "foreground": "hsl(var(--card-foreground))"
            }
        },
        "borderRadius": {
            "sm": "calc(var(--radius) - 6px)",
            "DEFAULT": "var(--radius - 4px)",
            "md": "calc(var(--radius) - 2px)",
            "lg": "var(--radius)",
            "xl": "calc(var(--radius) + 4px)",
            "2xl": "calc(var(--radius) + 8px)",
            "3xl": "calc(var(--radius) + 12px)"
        },
        "keyframes": {
            "accordion-down": {
                "from": {
                    "height": "0"
                },
                "to": {
                    "height": "var(--radix-accordion-content-height)"
                }
            },
            "accordion-up": {
                "from": {
                    "height": "var(--radix-accordion-content-height)"
                },
                "to": {
                    "height": "0"
                }
            },
            "slide-from-left": {
                "0%": {
                    "transform": "translateX(-100%)"
                },
                "100%": {
                    "transform": "translateX(0)"
                }
            },
            "slide-to-left": {
                "0%": {
                    "transform": "translateX(0)"
                },
                "100%": {
                    "transform": "translateX(-100%)"
                }
            }
        },
        "animation": {
            "slide-from-left": "slide-from-left 0.3s cubic-bezier(0.82, 0.085, 0.395, 0.895)",
            "slide-to-left": "slide-to-left 0.25s cubic-bezier(0.82, 0.085, 0.395, 0.895)",
            "accordion-down": "accordion-down 0.2s ease-out",
            "accordion-up": "accordion-up 0.2s ease-out"
        }
    }
},
  plugins: [require("tailwindcss-animate")],
}
