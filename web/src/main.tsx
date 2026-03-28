import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@radix-ui/themes/styles.css";
import { Theme } from "@radix-ui/themes";
import { AuthProvider } from "@/hooks/useAuth";
import { App } from "@/App";
import "@/i18n";
import { ThemeProvider } from "next-themes";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider attribute="class">
        <Theme accentColor="blue" grayColor="slate" radius="medium">
          <AuthProvider>
            <App />
          </AuthProvider>
        </Theme>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>,
);
