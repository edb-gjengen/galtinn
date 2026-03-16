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
import type { User } from "@/types";

interface EditProfileFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  date_of_birth: string;
  street_address: string;
  street_address_two: string;
  postal_code: string;
  city: string;
  country: string;
}

export function EditProfile() {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [generalError, setGeneralError] = useState("");

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<EditProfileFormData>({
    defaultValues: {
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
      email: user?.email ?? "",
      phone_number: user?.phone_number ?? "",
      date_of_birth: user?.date_of_birth ?? "",
      street_address: user?.street_address ?? "",
      street_address_two: user?.street_address_two ?? "",
      postal_code: user?.postal_code ?? "",
      city: user?.city ?? "",
      country: user?.country ?? "NO",
    },
  });

  if (!user) return null;

  const onSubmit = async (data: EditProfileFormData) => {
    setGeneralError("");
    try {
      await fetchApi<User>("/api/me/update/", {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      await refreshUser();
      navigate("/me/");
    } catch (err) {
      if (err instanceof ApiError) {
        for (const [key, value] of Object.entries(err.data)) {
          if (key === "detail") {
            setGeneralError(String(value));
          } else if (Array.isArray(value) && key in data) {
            setError(key as keyof EditProfileFormData, {
              message: value.map(String).join(" "),
            });
          }
        }
      } else {
        setGeneralError(t("registrationFailed"));
      }
    }
  };

  const fields: {
    name: keyof EditProfileFormData;
    label: string;
    type: "text" | "email" | "tel" | "date";
    required?: boolean;
  }[] = [
    { name: "first_name", label: t("firstName"), type: "text", required: true },
    { name: "last_name", label: t("lastName"), type: "text", required: true },
    { name: "email", label: t("email"), type: "email", required: true },
    { name: "phone_number", label: t("phoneNumber"), type: "tel" },
    { name: "date_of_birth", label: t("dateOfBirth"), type: "date" },
    { name: "street_address", label: t("streetAddress"), type: "text" },
    { name: "street_address_two", label: t("streetAddressTwo"), type: "text" },
    { name: "postal_code", label: t("postalCode"), type: "text" },
    { name: "city", label: t("city"), type: "text" },
    { name: "country", label: t("country"), type: "text" },
  ];

  return (
    <Flex justify="center" pt="5">
      <Box style={{ width: "100%", maxWidth: 480 }}>
        <Card size="4">
          <form onSubmit={handleSubmit(onSubmit)}>
            <Flex direction="column" gap="4">
              <Heading size="5" align="center">
                {t("editProfile")}
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
                    mt="1"
                    color={errors[field.name] ? "red" : undefined}
                    {...register(field.name, {
                      required: field.required,
                    })}
                  />
                  {errors[field.name]?.message && (
                    <Text size="1" color="red" mt="1">
                      {errors[field.name]?.message}
                    </Text>
                  )}
                </Box>
              ))}

              <Flex gap="3">
                <Button type="submit" size="3" style={{ flex: 1 }} disabled={isSubmitting}>
                  {t("save")}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="3"
                  onClick={() => navigate("/me/")}
                >
                  {t("cancel")}
                </Button>
              </Flex>
            </Flex>
          </form>
        </Card>
      </Box>
    </Flex>
  );
}
