import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
import { ApiError } from "@/lib/api";

export function Register() {
  const { t } = useTranslation();
  const { register } = useAuth();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    password: "",
  });
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [generalError, setGeneralError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setGeneralError("");
    setLoading(true);

    try {
      await register(form);
    } catch (err) {
      if (err instanceof ApiError) {
        const fieldErrors: Record<string, string[]> = {};
        for (const [key, value] of Object.entries(err.data)) {
          if (key === "detail") {
            setGeneralError(String(value));
          } else if (key === "non_field_errors") {
            setGeneralError((value as string[]).join(" "));
          } else if (Array.isArray(value)) {
            fieldErrors[key] = value.map(String);
          }
        }
        setErrors(fieldErrors);
        if (!Object.keys(fieldErrors).length && !generalError) {
          setGeneralError(t("registrationFailed"));
        }
      } else {
        setGeneralError(t("registrationFailed"));
      }
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { name: "first_name", label: t("firstName"), type: "text", autoComplete: "given-name" },
    { name: "last_name", label: t("lastName"), type: "text", autoComplete: "family-name" },
    { name: "email", label: t("email"), type: "email", autoComplete: "email" },
    { name: "phone_number", label: t("phoneNumber"), type: "tel", autoComplete: "tel" },
    { name: "password", label: t("password"), type: "password", autoComplete: "new-password" },
  ] as const;

  return (
    <Flex justify="center" pt="9">
      <Box style={{ width: "100%", maxWidth: 420 }}>
        <Card size="4">
          <form onSubmit={handleSubmit}>
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
                    value={form[field.name]}
                    onChange={handleChange(field.name)}
                    required
                    autoComplete={field.autoComplete}
                    mt="1"
                    color={errors[field.name] ? "red" : undefined}
                  />
                  {errors[field.name] && (
                    <Text size="1" color="red" mt="1">
                      {errors[field.name].join(" ")}
                    </Text>
                  )}
                </Box>
              ))}

              <Button type="submit" size="3" disabled={loading}>
                {t("register")}
              </Button>

              <Text size="2" align="center" color="gray">
                {t("alreadyHaveAccount")}{" "}
                <Link to="/login/">{t("loginHere")}</Link>
              </Text>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
