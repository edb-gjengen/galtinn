import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Button, Callout, Card, Flex, Grid, Heading, Text } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { fetchApi } from "@/lib/api";
import type { OrgUnit } from "@/types";

export function VolunteerHome() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [myOrgs, setMyOrgs] = useState<OrgUnit[]>([]);

  useEffect(() => {
    if (user?.is_volunteer) {
      fetchApi<OrgUnit[]>("/api/volunteer/orgunits/mine/").then(setMyOrgs);
    }
  }, [user]);

  if (!user) return null;

  const isVolunteer = user.is_volunteer;

  if (!isVolunteer) {
    return (
      <Box>
        <Heading size="6" mb="4">
          {t("volunteer")}
        </Heading>
        <Callout.Root>
          <Callout.Text>{t("notVolunteerMessage")}</Callout.Text>
        </Callout.Root>
        <Box mt="4">
          <Button size="3" asChild>
            <a
              href={
                i18n.language === "nb"
                  ? "https://studentersamfundet.no/bli-aktiv/"
                  : "https://studentersamfundet.no/bli-aktiv/become-a-volunteer/"
              }
            >
              {t("becomeVolunteer")}
            </a>
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Heading size="6" mb="2">
        {t("volunteer")}
      </Heading>
      <Text size="2" color="gray" mb="5" as="p">
        {t("volunteerSection")}
      </Text>

      <Grid columns={{ initial: "1", md: "2" }} gap="5" mb="5">
        <Card>
          <Flex direction="column" gap="3">
            <Heading size="4">{t("orgUnitList")}</Heading>
            <Text size="2" color="gray">
              {t("orgUnitListDescription")}
            </Text>
            <Button variant="outline" asChild>
              <Link to="/orgunits/">{t("showOrgUnits")}</Link>
            </Button>
          </Flex>
        </Card>
      </Grid>

      {myOrgs.length > 0 && (
        <>
          <Heading size="4" mb="3">
            {t("yourOrganizations")}
          </Heading>
          <Flex direction="column" gap="3" mb="5">
            {myOrgs.map((org) => (
              <Card key={org.id}>
                <Flex justify="between" align="center" wrap="wrap" gap="3">
                  <Link to={`/orgunit/${org.slug}/`} style={{ textDecoration: "none" }}>
                    <Text weight="bold" highContrast>
                      {org.name}
                    </Text>
                  </Link>
                  <Flex gap="2">
                    <Button size="1" variant="outline" asChild>
                      <Link to={`/orgunit/edit/users/${org.slug}/`}>{t("manageMembers")}</Link>
                    </Button>
                    <Button size="1" variant="outline" asChild>
                      <Link to={`/orgunit/edit/${org.slug}/`}>{t("edit")}</Link>
                    </Button>
                  </Flex>
                </Flex>
              </Card>
            ))}
          </Flex>
        </>
      )}
    </Box>
  );
}
