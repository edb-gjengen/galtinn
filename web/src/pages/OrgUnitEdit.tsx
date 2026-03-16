import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { Box, Button, Callout, Card, Flex, Heading, Text, TextArea, TextField } from "@radix-ui/themes";
import { fetchApi, ApiError } from "@/lib/api";
import type { OrgUnit } from "@/types";

interface OrgUnitEditFormData {
  name: string;
  short_name: string;
  email: string;
  website: string;
  description: string;
}

export function OrgUnitEdit() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [orgunit, setOrgunit] = useState<OrgUnit | null>(null);
  const [generalError, setGeneralError] = useState("");
  const [loaded, setLoaded] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<OrgUnitEditFormData>();

  useEffect(() => {
    if (!slug) return;
    fetchApi<OrgUnit>(`/api/volunteer/orgunits/${slug}/`).then((data) => {
      setOrgunit(data);
      reset({
        name: data.name,
        short_name: data.short_name,
        email: data.email,
        website: data.website,
        description: data.description,
      });
      setLoaded(true);
    });
  }, [slug, reset]);

  if (!loaded || !orgunit) return null;

  const onSubmit = async (data: OrgUnitEditFormData) => {
    setGeneralError("");
    try {
      await fetchApi(`/api/volunteer/orgunits/${slug}/update/`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      navigate(`/orgunit/${slug}/`);
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
      <Box style={{ width: "100%", maxWidth: 500 }}>
        <Card size="4">
          <form onSubmit={handleSubmit(onSubmit)}>
            <Flex direction="column" gap="4">
              <Heading size="5" align="center">
                {t("editOrgUnit")}
              </Heading>

              {generalError && (
                <Callout.Root color="red">
                  <Callout.Text>{generalError}</Callout.Text>
                </Callout.Root>
              )}

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="name">
                  {t("name")}
                </Text>
                <TextField.Root
                  id="name"
                  mt="1"
                  color={errors.name ? "red" : undefined}
                  {...register("name", { required: true })}
                />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="short_name">
                  {t("shortName")}
                </Text>
                <TextField.Root id="short_name" mt="1" {...register("short_name")} />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="email">
                  {t("email")}
                </Text>
                <TextField.Root id="email" type="email" mt="1" {...register("email")} />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="website">
                  {t("website")}
                </Text>
                <TextField.Root id="website" type="url" mt="1" {...register("website")} />
              </Box>

              <Box>
                <Text as="label" size="2" weight="medium" htmlFor="description">
                  {t("description")}
                </Text>
                <TextArea id="description" mt="1" rows={4} {...register("description")} />
              </Box>

              <Flex gap="3">
                <Button type="submit" size="3" style={{ flex: 1 }} disabled={isSubmitting}>
                  {t("save")}
                </Button>
                <Button type="button" variant="outline" size="3" onClick={() => navigate(`/orgunit/${slug}/`)}>
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
