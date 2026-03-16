import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import {
  Box,
  Button,
  Callout,
  Card,
  Flex,
  Heading,
  Text,
  TextField,
} from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { fetchApi, ApiError } from "@/lib/api";

interface DeleteAccountFormData {
  username: string;
}

export function DeleteAccount() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [generalError, setGeneralError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DeleteAccountFormData>();

  if (!user) return null;

  const onSubmit = async (data: DeleteAccountFormData) => {
    setGeneralError("");
    if (data.username !== user.username) {
      return;
    }
    try {
      await fetchApi<void>("/api/me/delete/", {
        method: "DELETE",
      });
      navigate("/login/");
    } catch (err) {
      if (err instanceof ApiError && err.data.detail) {
        setGeneralError(String(err.data.detail));
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
              <Heading size="5" align="center" color="red">
                {t("deleteAccount")}
              </Heading>

              <Callout.Root color="red">
                <Callout.Text>{t("deleteAccountConfirm")}</Callout.Text>
              </Callout.Root>

              {generalError && (
                <Callout.Root color="red">
                  <Callout.Text>{generalError}</Callout.Text>
                </Callout.Root>
              )}

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="username">
                  {t("typeUsernameToConfirm")}
                </Text>
                <TextField.Root
                  id="username"
                  mt="1"
                  color={errors.username ? "red" : undefined}
                  {...register("username", {
                    required: true,
                    validate: (v) => v === user.username || t("typeUsernameToConfirm"),
                  })}
                />
                {errors.username?.message && (
                  <Text size="1" color="red" mt="1">
                    {errors.username.message}
                  </Text>
                )}
              </Box>

              <Button type="submit" size="3" color="red" disabled={isSubmitting}>
                {t("deleteAccountButton")}
              </Button>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
