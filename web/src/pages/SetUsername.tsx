import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Box, Button, Callout, Card, Flex, Heading, Text, TextField } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { fetchApi, ApiError } from "@/lib/api";

interface SetUsernameFormData {
  username: string;
}

export function SetUsername() {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [generalError, setGeneralError] = useState("");

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<SetUsernameFormData>();

  if (!user) return null;

  if (user.has_set_username) {
    return <Navigate to="/me/" replace />;
  }

  const onSubmit = async (data: SetUsernameFormData) => {
    setGeneralError("");
    try {
      await fetchApi<void>("/api/me/set-username/", {
        method: "POST",
        body: JSON.stringify(data),
      });
      await refreshUser();
      navigate("/me/");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.data.username) {
          setError("username", {
            message: Array.isArray(err.data.username)
              ? err.data.username.map(String).join(" ")
              : String(err.data.username),
          });
        } else if (err.data.detail) {
          setGeneralError(String(err.data.detail));
        }
      } else {
        setGeneralError(String(err));
      }
    }
  };

  return (
    <Flex justify="center" pt="5">
      <Box style={{ width: "100%", maxWidth: 400 }}>
        <Card size="4">
          <form onSubmit={handleSubmit(onSubmit)}>
            <Flex direction="column" gap="4">
              <Heading size="5" align="center">
                {t("setUsername")}
              </Heading>

              <Callout.Root color="yellow">
                <Callout.Text>{t("usernameCanOnlyBeSetOnce")}</Callout.Text>
              </Callout.Root>

              {generalError && (
                <Callout.Root color="red">
                  <Callout.Text>{generalError}</Callout.Text>
                </Callout.Root>
              )}

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="username">
                  {t("username")}
                </Text>
                <TextField.Root
                  id="username"
                  mt="1"
                  color={errors.username ? "red" : undefined}
                  {...register("username", { required: true })}
                />
                <Text size="1" color="gray" mt="1">
                  {t("usernameHelp")}
                </Text>
                {errors.username?.message && (
                  <Text size="1" color="red" mt="1">
                    {errors.username.message}
                  </Text>
                )}
              </Box>

              <Button type="submit" size="3" disabled={isSubmitting}>
                {t("setUsername")}
              </Button>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
