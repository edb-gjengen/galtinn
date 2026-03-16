import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Button, Flex, Heading, Text } from "@radix-ui/themes";

export function NotFound() {
  const { t } = useTranslation();

  return (
    <Flex justify="center" align="center" pt="9">
      <Box style={{ textAlign: "center" }}>
        <Heading size="8" mb="3">
          404
        </Heading>
        <Heading size="4" mb="2">
          {t("pageNotFound")}
        </Heading>
        <Text size="3" color="gray" mb="5" as="p">
          {t("pageNotFoundMessage")}
        </Text>
        <Flex gap="3" justify="center" mt="5">
          <Button asChild>
            <Link to="/home/">{t("goHome")}</Link>
          </Button>
          <Button variant="outline" asChild>
            <a href="/">{t("goToOldSite")}</a>
          </Button>
        </Flex>
      </Box>
    </Flex>
  );
}
