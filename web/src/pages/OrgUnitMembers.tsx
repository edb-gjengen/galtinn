import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Badge, Box, Button, Callout, Card, Flex, Heading, Text, TextField } from "@radix-ui/themes";
import { fetchApi } from "@/lib/api";
import type { OrgUnit, OrgUnitMember, OrgUnitMembersResponse, UserSearchResult } from "@/types";

export function OrgUnitMembers() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const [orgunit, setOrgunit] = useState<OrgUnit | null>(null);
  const [members, setMembers] = useState<OrgUnitMember[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);

  const loadMembers = useCallback(() => {
    if (!slug) return;
    fetchApi<OrgUnitMembersResponse>(`/api/volunteer/orgunits/${slug}/members/`).then((data) => {
      setMembers(data.members);
      setIsAdmin(data.is_admin);
    });
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    fetchApi<OrgUnit>(`/api/volunteer/orgunits/${slug}/`).then(setOrgunit);
    loadMembers();
  }, [slug, loadMembers]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (searchQuery.length < 2) {
        setSearchResults([]);
        return;
      }
      fetchApi<UserSearchResult[]>(`/api/volunteer/users/search/?q=${encodeURIComponent(searchQuery)}`).then(
        setSearchResults,
      );
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  const addMember = async (userId: number, role: "member" | "admin") => {
    if (!slug) return;
    await fetchApi(`/api/volunteer/orgunits/${slug}/members/add/`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, role }),
    });
    setSearchQuery("");
    setSearchResults([]);
    loadMembers();
  };

  const removeMember = async (userId: number) => {
    if (!slug) return;
    if (!confirm(t("removeUserConfirm"))) return;
    await fetchApi(`/api/volunteer/orgunits/${slug}/members/remove/`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    });
    loadMembers();
  };

  const toggleRole = async (member: OrgUnitMember) => {
    if (!slug) return;
    if (member.is_admin) {
      await fetchApi(`/api/volunteer/orgunits/${slug}/members/add/`, {
        method: "POST",
        body: JSON.stringify({ user_id: member.id, role: "member" }),
      });
    } else {
      await fetchApi(`/api/volunteer/orgunits/${slug}/members/add/`, {
        method: "POST",
        body: JSON.stringify({ user_id: member.id, role: "admin" }),
      });
    }
    loadMembers();
  };

  if (!orgunit) return null;

  if (!isAdmin) {
    return (
      <Box style={{ maxWidth: 700, margin: "0 auto" }}>
        <Callout.Root color="red">
          <Callout.Text>{t("notAuthorized")}</Callout.Text>
        </Callout.Root>
      </Box>
    );
  }

  const hasDistinctAdminGroup = orgunit.group !== orgunit.admin_group;

  return (
    <Box style={{ maxWidth: 700, margin: "0 auto" }}>
      <Heading size="5" mb="4">
        {orgunit.name} — {t("manageMembers")}
      </Heading>

      {/* User search */}
      <Card mb="4">
        <Flex direction="column" gap="3">
          <TextField.Root
            placeholder={t("searchUsers")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchResults.length > 0 && (
            <Flex direction="column" gap="2">
              {searchResults.map((u) => (
                <Flex key={u.id} justify="between" align="center" gap="2">
                  <Text size="2">
                    {u.first_name} {u.last_name} ({u.email})
                  </Text>
                  <Flex gap="2">
                    {hasDistinctAdminGroup && (
                      <Button size="1" variant="soft" onClick={() => addMember(u.id, "member")}>
                        {t("addMember")}
                      </Button>
                    )}
                    <Button size="1" variant="soft" onClick={() => addMember(u.id, "admin")}>
                      {t("addAdmin")}
                    </Button>
                  </Flex>
                </Flex>
              ))}
            </Flex>
          )}
        </Flex>
      </Card>

      {/* Members list */}
      {members.length === 0 ? (
        <Text color="gray">{t("noMembers")}</Text>
      ) : (
        <Flex direction="column" gap="2">
          {members.map((m) => (
            <Card key={m.id}>
              <Flex justify="between" align="center" wrap="wrap" gap="2">
                <Flex align="center" gap="2" wrap="wrap">
                  <Text weight="bold">
                    {m.first_name} {m.last_name}
                  </Text>
                  <Text size="1" color="gray">
                    {m.email}
                  </Text>
                  {m.is_admin && <Badge color="blue">{t("admin")}</Badge>}
                  <MembershipBadge member={m} />
                </Flex>
                <Flex gap="2">
                  {hasDistinctAdminGroup && (
                    <Button size="1" variant="outline" onClick={() => toggleRole(m)}>
                      {m.is_admin ? t("makeMember") : t("makeAdmin")}
                    </Button>
                  )}
                  <Button size="1" variant="outline" color="red" onClick={() => removeMember(m.id)}>
                    {t("remove")}
                  </Button>
                </Flex>
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
