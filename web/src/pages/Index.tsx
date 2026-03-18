import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Box, Button, Callout, Card, Flex, Grid, Heading, Text, TextField } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";

interface LoginFormData {
  email: string;
  password: string;
}

export function Index() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const [error, setError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<LoginFormData>();

  const onSubmit = async (data: LoginFormData) => {
    setError("");
    try {
      await login(data.email, data.password);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail ? String(err.data.detail) : t("loginFailed"));
      } else {
        setError(t("loginFailed"));
      }
    }
  };

  return (
    <Flex justify="center" pt="9">
      <Box style={{ width: "100%", maxWidth: 800 }}>
        <Grid columns={{ initial: "1", md: "2" }} gap="6">
          <Flex direction="column" justify="center" gap="4">
            <Heading size="6">{t("welcomeGreeting")} 👋</Heading>
            <Text size="3">
              {t("welcomeMessage")} <a href="https://studentersamfundet.no">{t("chateauNeuf")}</a>.
            </Text>
            <Box>
              <Button size="3" asChild>
                <Link to="/register/">{t("becomeMember")}</Link>
              </Button>
            </Box>
          </Flex>

          <Card size="4">
            <form onSubmit={handleSubmit(onSubmit)}>
              <Flex direction="column" gap="4">
                <Box>
                  <Text size="2" color="gray">
                    {t("alreadyMember")}
                  </Text>
                  <Heading size="4">{t("loginHere")}</Heading>
                </Box>

                {error && (
                  <Callout.Root color="red">
                    <Callout.Text>{error}</Callout.Text>
                  </Callout.Root>
                )}

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

                <Box>
                  <Text as="label" size="2" weight="medium" htmlFor="password">
                    {t("password")}
                  </Text>
                  <TextField.Root
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    mt="1"
                    {...register("password", { required: true })}
                  />
                </Box>

                <Button type="submit" size="3" disabled={isSubmitting}>
                  {t("login")}
                </Button>
              </Flex>
            </form>
          </Card>
        </Grid>
      </Box>
    </Flex>
  );
}
