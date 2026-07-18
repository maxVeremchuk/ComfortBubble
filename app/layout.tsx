import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Comfort Bubble · HVAC Digital Twin",
  description: "A location-aware HVAC simulation that follows the person, not the thermostat.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
