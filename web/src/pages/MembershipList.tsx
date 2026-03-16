import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Badge,
  Box,
  Callout,
  Heading,
  Table,
  Text,
} from "@radix-ui/themes";
import { fetchApi } from "@/lib/api";
import type { Membership } from "@/types";

export function MembershipList() {
  const { t } = useTranslation();
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchApi<Membership[]>("/api/me/memberships/")
      .then(setMemberships)
      .catch(() => setError(t("registrationFailed")))
      .finally(() => setLoading(false));
  }, [t]);

  return (
    <Box style={{ maxWidth: 700, margin: "0 auto" }}>
      <Heading size="5" mb="4">
        {t("membershipHistory")}
      </Heading>

      {error && (
        <Callout.Root color="red" mb="4">
          <Callout.Text>{error}</Callout.Text>
        </Callout.Root>
      )}

      {loading && <Text>{t("home")}...</Text>}

      {!loading && memberships.length === 0 && (
        <Callout.Root>
          <Callout.Text>{t("noMemberships")}</Callout.Text>
        </Callout.Root>
      )}

      {!loading && memberships.length > 0 && (
        <Table.Root>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeaderCell>{t("type")}</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>{t("startDate")}</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>{t("endDate")}</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>{t("status")}</Table.ColumnHeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {memberships.map((m) => (
              <Table.Row key={m.id}>
                <Table.Cell>{m.membership_type}</Table.Cell>
                <Table.Cell>{m.start_date}</Table.Cell>
                <Table.Cell>{m.end_date ?? t("lifelong")}</Table.Cell>
                <Table.Cell>
                  {m.is_valid ? (
                    <Badge color="green">{t("valid")}</Badge>
                  ) : (
                    <Badge color="red">{t("expired")}</Badge>
                  )}
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      )}
    </Box>
  );
}
