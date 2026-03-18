import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Badge, Box, Button, Card, Flex, Grid, Heading, RadioCards, Text } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { fetchApi, getCsrfToken } from "@/lib/api";
import type { MembershipType } from "@/types";

export function Home() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [emailSent, setEmailSent] = useState(false);
  const [membershipTypes, setMembershipTypes] = useState<MembershipType[]>([]);
  const [selectedMembershipType, setSelectedMembershipType] = useState<string>("");

  useEffect(() => {
    fetchApi<MembershipType[]>("/api/membership-types/").then((types) => {
      setMembershipTypes(types);
      const defaultType = types.find((mt) => mt.is_default) ?? types[0];
      if (defaultType) {
        setSelectedMembershipType(defaultType.slug);
      }
    });
  }, []);

  if (!user) return null;

  const membership = user.last_membership;
  const hasValidMembership = membership?.is_valid ?? false;
  const expiringSoon = membership?.expires_in_less_than_one_month ?? false;

  const handleResendEmail = async () => {
    await fetchApi("/api/user/resend_validation_email/", { method: "POST" });
    setEmailSent(true);
  };

  return (
    <Box>
      <Heading size="6" mb="5">
        {t("home")}
      </Heading>

      <Grid columns={{ initial: "1", md: "2" }} gap="5">
        {/* Membership Card */}
        <Card>
          <Flex direction="column" gap="3">
            <Heading size="4">{t("yourMembership")}</Heading>
            <Text size="2" color="gray">
              {t("membershipStatus")}
            </Text>

            {hasValidMembership && !expiringSoon && (
              <Box
                p="3"
                style={{
                  backgroundColor: "var(--green-3)",
                  borderRadius: "var(--radius-2)",
                }}
              >
                <Text color="green" weight="medium">
                  {t("validMembership")}
                </Text>
              </Box>
            )}

            {hasValidMembership && expiringSoon && (
              <Box
                p="3"
                style={{
                  backgroundColor: "var(--yellow-3)",
                  borderRadius: "var(--radius-2)",
                }}
              >
                <Text color="yellow" weight="medium">
                  {t("membershipExpiringSoon")}
                </Text>
              </Box>
            )}

            {!hasValidMembership && membership && (
              <Box
                p="3"
                style={{
                  backgroundColor: "var(--red-3)",
                  borderRadius: "var(--radius-2)",
                }}
              >
                <Text color="red" weight="medium">
                  {t("membershipExpired")}
                </Text>
              </Box>
            )}

            {!membership && (
              <Box
                p="3"
                style={{
                  backgroundColor: "var(--gray-3)",
                  borderRadius: "var(--radius-2)",
                }}
              >
                <Text>{t("becomeMember")}</Text>
              </Box>
            )}

            {hasValidMembership && membership && (
              <Flex direction="column" gap="1">
                <Text size="2">
                  {t("validUntil")}: <Text weight="bold">{membership.end_date ?? t("lifelong")}</Text>
                </Text>
              </Flex>
            )}

            {(!hasValidMembership || expiringSoon) && membershipTypes.length > 0 && (
              <Flex direction="column" gap="3">
                <RadioCards.Root
                  value={selectedMembershipType}
                  onValueChange={setSelectedMembershipType}
                  columns={{ initial: "1", sm: String(membershipTypes.length) }}
                >
                  {membershipTypes.map((mt) => (
                    <RadioCards.Item key={mt.slug} value={mt.slug}>
                      <Flex direction="column" width="100%">
                        <Text weight="bold">{t(`membershipType.${mt.slug}`)}</Text>
                        <Text size="2" color="gray">
                          {mt.price_nok_kr} kr
                        </Text>
                      </Flex>
                    </RadioCards.Item>
                  ))}
                </RadioCards.Root>
                <form action="/api/stripe/checkout-session/" method="POST">
                  <input type="hidden" name="membership_type" value={selectedMembershipType} />
                  <input type="hidden" name="csrfmiddlewaretoken" value={getCsrfToken()} />
                  <Button type="submit" disabled={!selectedMembershipType} style={{ width: "100%" }}>
                    {t("buyMembership")}
                  </Button>
                </form>
              </Flex>
            )}
          </Flex>
        </Card>

        {/* Profile Card */}
        <Card>
          <Flex direction="column" gap="3">
            <Heading size="4">{t("yourProfile")}</Heading>
            <Text size="2" color="gray">
              {t("quickProfileView")}
            </Text>

            <Flex direction="column" gap="2">
              <Text size="2">
                {t("fullName")}:{" "}
                <Text weight="bold">
                  {user.first_name} {user.last_name}
                  {user.is_volunteer && ` (${user.username})`}
                </Text>
              </Text>

              <Flex align="center" gap="2" wrap="wrap">
                <Text size="2">
                  {t("email")}: <Text weight="bold">{user.email}</Text>
                </Text>
                {user.email_is_confirmed ? (
                  <Badge color="green">{t("validated")}</Badge>
                ) : (
                  <>
                    <Badge color="yellow">{t("notValidated")}</Badge>
                    <Button size="1" variant="soft" onClick={handleResendEmail} disabled={emailSent}>
                      {emailSent ? t("validationEmailSent") : t("resendValidationEmail")}
                    </Button>
                  </>
                )}
              </Flex>

              <Flex align="center" gap="2" wrap="wrap">
                <Text size="2">
                  {t("phoneNumber")}: <Text weight="bold">{user.phone_number || "-"}</Text>
                </Text>
                {user.phone_number ? (
                  user.phone_number_confirmed ? (
                    <Badge color="green">{t("validated")}</Badge>
                  ) : null
                ) : (
                  <Badge color="red">{t("missing")}</Badge>
                )}
              </Flex>
            </Flex>
          </Flex>
        </Card>

        {/* Password Card */}
        <Card>
          <Flex direction="column" gap="3">
            <Heading size="4">{t("changePassword")}</Heading>
            <Text size="2" color="gray">
              {t("changePasswordHint")}
            </Text>
            <Button variant="outline" asChild>
              <Link to="/auth/password_change/">{t("changePassword")}</Link>
            </Button>
          </Flex>
        </Card>

        {/* Username Card */}
        {!user.has_set_username && (
          <Card>
            <Flex direction="column" gap="3">
              <Heading size="4">{t("setUsername")}</Heading>
              <Text size="2" color="gray">
                {t("setUsernameHint")}
              </Text>
              <Button variant="outline" asChild>
                <Link to="/me/update/username/">{t("setUsername")}</Link>
              </Button>
            </Flex>
          </Card>
        )}
      </Grid>
    </Box>
  );
}
