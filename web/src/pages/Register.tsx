import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Box, Button, Callout, Card, Flex, Heading, Text, TextField } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";

interface RegisterFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  password: string;
}

export function Register() {
  const { t } = useTranslation();
  const { register: registerUser } = useAuth();
  const [generalError, setGeneralError] = useState("");

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>();

  const onSubmit = async (data: RegisterFormData) => {
    setGeneralError("");

    try {
      await registerUser(data);
    } catch (err) {
      if (err instanceof ApiError) {
        let hasFieldErrors = false;
        for (const [key, value] of Object.entries(err.data)) {
          if (key === "detail") {
            setGeneralError(String(value));
          } else if (key === "non_field_errors") {
            setGeneralError((value as string[]).join(" "));
          } else if (Array.isArray(value) && key in data) {
            setError(key as keyof RegisterFormData, {
              message: value.map(String).join(" "),
            });
            hasFieldErrors = true;
          }
        }
        if (!hasFieldErrors && !generalError) {
          setGeneralError(t("registrationFailed"));
        }
      } else {
        setGeneralError(t("registrationFailed"));
      }
    }
  };

  const fields: {
    name: keyof RegisterFormData;
    label: string;
    type: "text" | "email" | "tel" | "password";
    autoComplete: string;
  }[] = [
    { name: "first_name", label: t("firstName"), type: "text", autoComplete: "given-name" },
    { name: "last_name", label: t("lastName"), type: "text", autoComplete: "family-name" },
    { name: "email", label: t("email"), type: "email", autoComplete: "email" },
    { name: "phone_number", label: t("phoneNumber"), type: "tel", autoComplete: "tel" },
    { name: "password", label: t("password"), type: "password", autoComplete: "new-password" },
  ];

  return (
    <Flex justify="center" pt="9">
      <Box style={{ width: "100%", maxWidth: 420 }}>
        <Card size="4">
          <form onSubmit={handleSubmit(onSubmit)}>
            <Flex direction="column" gap="4">
              <Heading size="5" align="center">
                {t("register")}
              </Heading>

              {generalError && (
                <Callout.Root color="red">
                  <Callout.Text>{generalError}</Callout.Text>
                </Callout.Root>
              )}

              {fields.map((field) => (
                <Box key={field.name}>
                  <Text as="label" size="2" weight="medium" htmlFor={field.name}>
                    {field.label}
                  </Text>
                  <TextField.Root
                    id={field.name}
                    type={field.type}
                    autoComplete={field.autoComplete}
                    mt="1"
                    color={errors[field.name] ? "red" : undefined}
                    {...register(field.name, { required: true })}
                  />
                  {errors[field.name]?.message && (
                    <Text size="1" color="red" mt="1">
                      {errors[field.name]?.message}
                    </Text>
                  )}
                </Box>
              ))}

              <Button type="submit" size="3" disabled={isSubmitting}>
                {t("register")}
              </Button>

              <Text size="2" align="center" color="gray">
                {t("alreadyHaveAccount")} <Link to="/login/v2">{t("loginHere")}</Link>
              </Text>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
