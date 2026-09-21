import { I18nProvider } from "@/lib/i18n";
import { AuthProvider } from "@/lib/auth-context";

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <I18nProvider>
        {children}
      </I18nProvider>
    </AuthProvider>
  );
}
