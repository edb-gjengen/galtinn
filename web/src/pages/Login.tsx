import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Button, Callout, Card, Flex, Heading, Text, TextField } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";

export function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.detail ? String(err.data.detail) : t("loginFailed"));
      } else {
        setError(t("loginFailed"));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex justify="center" pt="9">
      <Box style={{ width: "100%", maxWidth: 420 }}>
        <Card size="4">
          <form onSubmit={handleSubmit}>
            <Flex direction="column" gap="4">
              <Heading size="5" align="center">
                {t("login")}
              </Heading>

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
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  mt="1"
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="password">
                  {t("password")}
                </Text>
                <TextField.Root
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  mt="1"
                />
                <Text size="1" align="center">
                  <Link to="/auth/password_reset/">{t("forgotPassword")}</Link>
                </Text>
              </Box>

              <Button type="submit" size="3" disabled={loading}>
                {t("login")}
              </Button>

              <Text size="2" align="center" color="gray">
                {t("noAccountYet")} <Link to="/register/">{t("registerHere")}</Link>
              </Text>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
