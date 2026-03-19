import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Heading } from "@radix-ui/themes";
import { fetchApi } from "@/lib/api";
import { NotFound } from "@/pages/NotFound";

interface FlatPageData {
  url: string;
  title: string;
  content: string;
}

export function FlatPage() {
  const { "*": pagePath } = useParams();
  const [page, setPage] = useState<FlatPageData | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!pagePath) return;
    let cancelled = false;
    const fetchPage = async () => {
      try {
        const data = await fetchApi<FlatPageData>(`/api/flatpages/${pagePath}`);
        if (!cancelled) setPage(data);
      } catch {
        console.error("Failed to fetch flat page with path:", pagePath);
        if (!cancelled) setNotFound(true);
      }
    };
    fetchPage();
    return () => {
      cancelled = true;
    };
  }, [pagePath]);

  if (notFound) return <NotFound />;
  if (!page) return null;

  return (
    <Box>
      <Heading size="6" mb="5">
        {page.title}
      </Heading>
      <div dangerouslySetInnerHTML={{ __html: page.content }} />
    </Box>
  );
}
