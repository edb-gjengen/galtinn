import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Card, Flex, Heading, Text } from "@radix-ui/themes";
import { fetchApi } from "@/lib/api";
import type { OrgUnit } from "@/types";

export function OrgUnitList() {
  const { t } = useTranslation();
  const [orgunits, setOrgunits] = useState<OrgUnit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<OrgUnit[]>("/api/volunteer/orgunits/")
      .then(setOrgunits)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box>
      <Heading size="6" mb="4">
        {t("orgUnitList")}
      </Heading>

      {loading && <Text>{t("view")}...</Text>}

      {!loading && (
        <Flex direction="column" gap="3">
          {orgunits.map((org) => (
            <Card key={org.id}>
              <Flex justify="between" align="center" wrap="wrap" gap="3">
                <Flex direction="column" gap="1">
                  <Link to={`/orgunit/${org.slug}/`} style={{ textDecoration: "none" }}>
                    <Text weight="bold" highContrast>
                      {org.name}
                    </Text>
                  </Link>
                  {org.email && (
                    <Text size="1" color="gray">
                      {org.email}
                    </Text>
                  )}
                </Flex>
                {org.contact_person && (
                  <Text size="2" color="gray">
                    {t("contactPerson")}: {org.contact_person.username}
                  </Text>
                )}
              </Flex>
            </Card>
          ))}
        </Flex>
      )}
    </Box>
  );
}
