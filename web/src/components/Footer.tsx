import { useTranslation } from "react-i18next";
import { Box, Container, Flex, Link, Separator, Text } from "@radix-ui/themes";
import dnsLogo from "@/assets/dns_ikon_svart.png";
import { useTheme } from "next-themes";

export function Footer() {
  const { t } = useTranslation();
  const { theme } = useTheme();

  return (
    <Box asChild mt="9" pb="5">
      <footer>
        <Container size="4" px="4">
          <Separator size="4" mb="5" />
          <Flex direction="column" align="center" gap="3">
            <Link href="https://studentersamfundet.no" title="Det Norske Studentersamfund">
              <img
                src={dnsLogo}
                width="63"
                height="75"
                style={{ filter: theme === "light" ? "invert(0)" : "invert(1)" }}
                alt="DNS"
              />
            </Link>
            <Text size="2" color="gray">
              {t("createdWith")}{" "}
              <Text size="2" color="pink" title="kærlighed">
                ♥
              </Text>{" "}
              {t("by")}{" "}
              <Link href="http://edb.technology/" color="gray">
                EDB-gjengen
              </Link>
            </Text>
          </Flex>
        </Container>
      </footer>
    </Box>
  );
}
