import { Outlet } from "react-router-dom";
import { Box, Container } from "@radix-ui/themes";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export function Layout() {
  return (
    <Box>
      <Navbar />
      <Container size="4" px="4" py="5">
        <Outlet />
      </Container>
      <Footer />
    </Box>
  );
}
