import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Badge, Box, Button, Card, Flex, Heading, Separator, Text } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { fetchApi } from "@/lib/api";

export function Profile() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [emailSent, setEmailSent] = useState(false);

  if (!user) return null;

  const membership = user.last_membership;

  const handleResendEmail = async () => {
    await fetchApi("/api/user/resend_validation_email/", { method: "POST" });
    setEmailSent(true);
  };

  return (
    <Box style={{ maxWidth: 600, margin: "0 auto" }}>
      <Heading size="5" mb="4">
        {t("yourProfile")}
      </Heading>

      <Card mb="4">
        <Flex direction="column" gap="2">
          <Text size="2">
            {t("fullName")}:{" "}
            <Text weight="bold">
              {user.first_name} {user.last_name}
            </Text>
          </Text>

          <Flex align="center" gap="2" wrap="wrap">
            <Text size="2">
              {t("username")}: <Text weight="bold">{user.username}</Text>
            </Text>
            {!user.has_set_username && (
              <>
                <Badge color="yellow">{t("usernameNotSet")}</Badge>
                <Button size="1" variant="soft" asChild>
                  <Link to="/me/update/username/">{t("setUsername")}</Link>
                </Button>
              </>
            )}
          </Flex>

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

          {(user.street_address || user.city) && (
            <Text size="2">
              {t("address")}:{" "}
              <Text weight="bold">
                {[user.street_address, user.street_address_two, user.postal_code, user.city].filter(Boolean).join(", ")}
              </Text>
            </Text>
          )}

          {user.date_of_birth && (
            <Text size="2">
              {t("dateOfBirth")}: <Text weight="bold">{user.date_of_birth}</Text>
            </Text>
          )}
        </Flex>
      </Card>

      <Card mb="4">
        <Flex direction="column" gap="2">
          <Flex align="center" gap="2">
            <Text size="2">
              {t("membership")}:{" "}
              {membership ? (
                <>
                  <Text weight="bold">{membership.end_date ?? t("lifelong")}</Text>{" "}
                  {membership.is_valid ? (
                    <Badge color="green">{t("valid")}</Badge>
                  ) : (
                    <Badge color="red">{t("expired")}</Badge>
                  )}
                </>
              ) : (
                <>
                  <Text weight="bold">{t("none")}</Text> <Badge color="red">{t("expired")}</Badge>
                </>
              )}
            </Text>
          </Flex>
        </Flex>
      </Card>

      <Flex gap="3" mb="4">
        <Button variant="outline" asChild>
          <Link to="/me/update/">{t("editProfile")}</Link>
        </Button>
      </Flex>

      <Separator size="4" my="4" />

      <Heading size="4" mb="3">
        {t("dangerZone")}
      </Heading>
      <Button variant="soft" color="red" asChild>
        <Link to="/me/delete/">{t("deleteAccount")}</Link>
      </Button>
    </Box>
  );
}
