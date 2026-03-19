import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Box, Button, Callout, Card, Flex, Heading, Text, TextField } from "@radix-ui/themes";
import { fetchApi } from "@/lib/api";

interface ForgotPasswordFormData {
  email: string;
}

export function ForgotPassword() {
  const { t } = useTranslation();
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<ForgotPasswordFormData>();

  const onSubmit = async (data: ForgotPasswordFormData) => {
    await fetchApi<void>("/api/auth/password/reset/", {
      method: "POST",
      body: JSON.stringify(data),
    });
    setSubmitted(true);
  };

  return (
    <Flex justify="center" pt="9">
      <Box style={{ width: "100%", maxWidth: 400 }}>
        <Card size="4">
          {submitted ? (
            <Flex direction="column" gap="4">
              <Heading size="5" align="center">
                {t("forgotPassword")}
              </Heading>
              <Callout.Root color="green">
                <Callout.Text>{t("passwordResetEmailSent")}</Callout.Text>
              </Callout.Root>
              <Button variant="outline" asChild>
                <Link to="/">{t("backToLogin")}</Link>
              </Button>
            </Flex>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)}>
              <Flex direction="column" gap="4">
                <Heading size="5" align="center">
                  {t("forgotPassword")}
                </Heading>
                <Text size="2" color="gray">
                  {t("forgotPasswordHint")}
                </Text>

                <Box>
                  <Text as="label" size="2" weight="medium" htmlFor="email">
                    {t("email")}
                  </Text>
                  <TextField.Root
                    id="email"
                    type="email"
                    autoComplete="email"
                    mt="1"
                    {...register("email", { required: true })}
                  />
                </Box>

                <Button type="submit" size="3" disabled={isSubmitting}>
                  {t("sendResetLink")}
                </Button>

                <Text size="2" align="center">
                  <Link to="/">{t("backToLogin")}</Link>
                </Text>
              </Flex>
            </form>
          )}
        </Card>
      </Box>
    </Flex>
  );
}
