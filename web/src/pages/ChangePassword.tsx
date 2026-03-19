import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Box, Button, Callout, Card, Flex, Heading, Text, TextField } from "@radix-ui/themes";
import { fetchApi, ApiError } from "@/lib/api";

interface ChangePasswordFormData {
  old_password: string;
  new_password: string;
}

export function ChangePassword() {
  const { t } = useTranslation();
  const [success, setSuccess] = useState(false);
  const [generalError, setGeneralError] = useState("");
  const [passwordHelpTexts, setPasswordHelpTexts] = useState<string[]>([]);

  useEffect(() => {
    let ignore = false;
    fetchApi<{ help_texts: string[] }>("/api/auth/password/validators/")
      .then((data) => {
        if (!ignore) {
          setPasswordHelpTexts(data.help_texts);
        }
      })
      .catch((err) => {
        console.error("Failed to fetch password help texts:", err);
      });
    return () => {
      ignore = true;
    };
  }, []);

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormData>();

  const onSubmit = async (data: ChangePasswordFormData) => {
    setGeneralError("");
    setSuccess(false);
    try {
      await fetchApi<void>("/api/auth/password/change/", {
        method: "POST",
        body: JSON.stringify(data),
      });
      setSuccess(true);
      reset();
    } catch (err) {
      if (err instanceof ApiError) {
        const d = err.data;
        if (d.old_password) {
          setError("old_password", {
            message: Array.isArray(d.old_password) ? d.old_password.map(String).join(" ") : String(d.old_password),
          });
        } else if (d.new_password) {
          setError("new_password", {
            message: Array.isArray(d.new_password) ? d.new_password.map(String).join(" ") : String(d.new_password),
          });
        } else if (d.detail) {
          setGeneralError(String(d.detail));
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
                {t("changePassword")}
              </Heading>

              {success && (
                <Callout.Root color="green">
                  <Callout.Text>{t("passwordChanged")}</Callout.Text>
                </Callout.Root>
              )}

              {generalError && (
                <Callout.Root color="red">
                  <Callout.Text>{generalError}</Callout.Text>
                </Callout.Root>
              )}

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="old_password">
                  {t("oldPassword")}
                </Text>
                <TextField.Root
                  id="old_password"
                  type="password"
                  mt="1"
                  color={errors.old_password ? "red" : undefined}
                  {...register("old_password", { required: true })}
                />
                {errors.old_password?.message && (
                  <Text size="1" color="red" mt="1">
                    {errors.old_password.message}
                  </Text>
                )}
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="new_password">
                  {t("newPassword")}
                </Text>
                <TextField.Root
                  id="new_password"
                  type="password"
                  mt="1"
                  color={errors.new_password ? "red" : undefined}
                  {...register("new_password", { required: true })}
                />
                {errors.new_password?.message && (
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
                {t("changePassword")}
              </Button>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
