import "@/styles/globals.css";
import { Inter, Fraunces } from "next/font/google";
import { useRouter } from "next/router";
import MainLayout from "@/layouts/MainLayout";
import ConsultantLayout from "@/layouts/ConsultantLayout";
import AdminLayout from "@/layouts/AdminLayout";
import { AuthProvider } from "@/hooks/useAuth";
import { ToastProvider } from "@/components/ui";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

// Staff shells get their own layout; other routes use the public shell.
export default function App({ Component, pageProps }) {
  const router = useRouter();
  const { pathname } = router;
  const isConsultantRoute =
    pathname === "/consultant" || pathname.startsWith("/consultant/");
  const isAdminRoute = pathname === "/admin" || pathname.startsWith("/admin/");
  const Shell = isConsultantRoute
    ? ConsultantLayout
    : isAdminRoute
      ? AdminLayout
      : MainLayout;

  return (
    <div className={`${inter.variable} ${fraunces.variable} font-sans antialiased`}>
      <AuthProvider>
        <ToastProvider>
          <Shell>
            <Component {...pageProps} />
          </Shell>
        </ToastProvider>
      </AuthProvider>
    </div>
  );
}
