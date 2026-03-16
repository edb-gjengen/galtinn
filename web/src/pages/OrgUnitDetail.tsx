import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Badge, Box, Button, Card, Flex, Heading, Text } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { fetchApi } from "@/lib/api";
import type { OrgUnit, OrgUnitMember, OrgUnitMembersResponse } from "@/types";

export function OrgUnitDetail() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const [orgunit, setOrgunit] = useState<OrgUnit | null>(null);
  const [members, setMembers] = useState<OrgUnitMember[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (!slug) return;
    fetchApi<OrgUnit>(`/api/volunteer/orgunits/${slug}/`).then(setOrgunit);
    fetchApi<OrgUnitMembersResponse>(`/api/volunteer/orgunits/${slug}/members/`).then((data) => {
      setMembers(data.members);
      setIsAdmin(data.is_admin);
    });
  }, [slug]);

  if (!orgunit || !user) return null;

  return (
    <Box style={{ maxWidth: 700, margin: "0 auto" }}>
      <Heading size="5" mb="2">
        {orgunit.name}
      </Heading>

      <Flex gap="3" mb="4" wrap="wrap">
        {orgunit.email && (
          <Text size="2">
            {t("email")}: <a href={`mailto:${orgunit.email}`}>{orgunit.email}</a>
          </Text>
        )}
        {orgunit.website && (
          <Text size="2">
            {t("website")}:{" "}
            <a href={orgunit.website} target="_blank" rel="noopener noreferrer">
              {orgunit.website}
            </a>
          </Text>
        )}
      </Flex>

      {orgunit.description && (
        <Text as="p" size="2" mb="4" color="gray">
          {orgunit.description}
        </Text>
      )}

      {isAdmin && (
        <Flex gap="2" mb="4">
          <Button variant="outline" size="2" asChild>
            <Link to={`/orgunit/edit/users/${slug}/`}>{t("manageMembers")}</Link>
          </Button>
          <Button variant="outline" size="2" asChild>
            <Link to={`/orgunit/edit/${slug}/`}>{t("edit")}</Link>
          </Button>
        </Flex>
      )}

      <Heading size="4" mb="3">
        {t("member")}
      </Heading>

      {members.length === 0 ? (
        <Text color="gray">{t("noMembers")}</Text>
      ) : (
        <Flex direction="column" gap="2">
          {members.map((m) => (
            <Card key={m.id}>
              <Flex justify="between" align="center" wrap="wrap" gap="2">
                <Flex align="center" gap="2">
                  <Text weight="bold">
                    {m.first_name} {m.last_name}
                  </Text>
                  <Text size="1" color="gray">
                    {m.email}
                  </Text>
                  {m.is_admin && <Badge color="blue">{t("admin")}</Badge>}
                </Flex>
                <MembershipBadge member={m} />
              </Flex>
            </Card>
          ))}
        </Flex>
      )}
    </Box>
  );
}

function MembershipBadge({ member }: { member: OrgUnitMember }) {
  const { t } = useTranslation();

  if (member.membership_is_valid) {
    return <Badge color="green">{member.membership_end_date ?? t("lifelong")}</Badge>;
  }
  if (member.membership_end_date) {
    return <Badge color="red">{member.membership_end_date}</Badge>;
  }
  return <Badge color="red">{t("none")}</Badge>;
}
