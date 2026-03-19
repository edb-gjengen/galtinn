import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Box, Button, Callout, Card, Flex, Heading, Text, TextField } from "@radix-ui/themes";
import { fetchApi, ApiError } from "@/lib/api";

interface ResetPasswordFormData {
  new_password: string;
}

export function ResetPasswordConfirm() {
  const { t } = useTranslation();
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const [success, setSuccess] = useState(false);
  const [generalError, setGeneralError] = useState("");
  const [passwordHelpTexts, setPasswordHelpTexts] = useState<string[]>([]);

  const fetchPasswordHelpTexts = async () => {
    try {
      const data = await fetchApi<{ help_texts: string[] }>("/api/auth/password/validators/");
      setPasswordHelpTexts(data.help_texts);
    } catch (err) {
      console.error("Failed to fetch password help texts:", err);
    }
  };

  useEffect(() => {
    fetchPasswordHelpTexts();
  }, []);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormData>();

  const onSubmit = async (data: ResetPasswordFormData) => {
    setGeneralError("");
    try {
      await fetchApi<void>("/api/auth/password/reset/confirm/", {
        method: "POST",
        body: JSON.stringify({ uid, token, new_password: data.new_password }),
      });
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        const d = err.data;
        if (d.new_password2) {
          setError("new_password", {
            message: Array.isArray(d.new_password2) ? d.new_password2.map(String).join(" ") : String(d.new_password2),
          });
        } else {
          setGeneralError(d.detail ? String(d.detail) : t("invalidResetLink"));
        }
      } else {
        setGeneralError(t("invalidResetLink"));
      }
    }
  };

  return (
    <Flex justify="center" pt="9">
      <Box style={{ width: "100%", maxWidth: 400 }}>
        <Card size="4">
          {success ? (
            <Flex direction="column" gap="4">
              <Heading size="5" align="center">
                {t("passwordChanged")}
              </Heading>
              <Callout.Root color="green">
                <Callout.Text>{t("passwordResetSuccess")}</Callout.Text>
              </Callout.Root>
              <Button asChild>
                <Link to="/">{t("backToLogin")}</Link>
              </Button>
            </Flex>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)}>
              <Flex direction="column" gap="4">
                <Heading size="5" align="center">
                  {t("setNewPassword")}
                </Heading>

                {generalError && (
                  <Callout.Root color="red">
                    <Callout.Text>{generalError}</Callout.Text>
                  </Callout.Root>
                )}

                <Box>
                  <Text as="label" size="2" weight="medium" htmlFor="new_password">
                    {t("newPassword")}
                  </Text>
                  <TextField.Root
                    id="new_password"
                    type="password"
                    autoComplete="new-password"
                    mt="1"
                    color={errors.new_password ? "red" : undefined}
                    {...register("new_password", { required: true })}
                  />
                  {errors.new_password && (
                    <Text size="1" color="red" mt="1">
                      {errors.new_password.message}
                    </Text>
                  )}
                  {passwordHelpTexts.length > 0 && (
                    <Flex direction="column" gap="1" mt="1">
                      {passwordHelpTexts.map((text, idx) => (
                        <Text key={idx} size="1" color="gray">
                          {text}
                        </Text>
                      ))}
                    </Flex>
                  )}
                </Box>

                <Button type="submit" size="3" disabled={isSubmitting}>
                  {t("setNewPassword")}
                </Button>
              </Flex>
            </form>
          )}
        </Card>
      </Box>
    </Flex>
  );
}
