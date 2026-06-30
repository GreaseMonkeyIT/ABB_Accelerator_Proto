import "./globals.css";
import { Saira_Semi_Condensed } from "next/font/google";

// VISR display face — a condensed industrial typeface for HUD chrome (brand, panel heads, stat
// values, micro-labels). This is a *placeholder* for the exact "Industrial" font (still to be
// confirmed). next/font self-hosts it into the static export, so the air-gap-portable build keeps
// working at runtime with no CDN. To swap the real font: replace this with next/font/local + the
// .woff2, keeping variable: "--font-display".
const display = Saira_Semi_Condensed({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

export const metadata = {
  title: "VISR · Causal AIOps",
  description: "Causal correlation verdict for a single-node Kubernetes factory.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={display.variable}>
      <body>{children}</body>
    </html>
  );
}
