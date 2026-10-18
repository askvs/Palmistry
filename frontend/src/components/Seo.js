import Head from "next/head";
import { useRouter } from "next/router";

const BASE = process.env.NEXT_PUBLIC_SITE_URL || "";

export default function Seo({
  title,
  description = "AI-guided palm and tarot readings for reflection, mindfulness, and personal growth.",
  path,
  ogImage = "/og-default.png",
}) {
  const router = useRouter();
  const url = `${BASE}${path || router.asPath.split("?")[0]}`;
  const fullTitle = title ? `${title} · MysticLens` : "MysticLens — Palm & Tarot Readings";
  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={url || undefined} />
      <meta name="theme-color" content="#F7F6FC" />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="website" />
      <meta property="og:url" content={url || undefined} />
      <meta property="og:image" content={ogImage} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
    </Head>
  );
}
