import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Button, Container, DropdownMenu, Flex, Separator, Text } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";
import GaltinnLogo from "@/assets/galtinn-logo-2024.svg?react";
import { useTheme } from "next-themes";
import { MoonIcon, SunIcon } from "@radix-ui/react-icons";

export function Navbar() {
  const { t, i18n } = useTranslation();
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === "nb" ? "en" : "nb";
    i18n.changeLanguage(newLang);
  };

  return (
    <Box px="4" py="4">
      <Container size="4">
        <Flex justify="between" align="center" gap="4">
          <Flex align="center" gap="4">
            <Link to={isAuthenticated ? "/home/" : "/"} style={{ textDecoration: "none" }}>
              <GaltinnLogo className="galtinn-logo" />
            </Link>

            {isAuthenticated && (
              <Flex gap="3" asChild>
                <nav>
                  <Link to="/memberships/" style={{ textDecoration: "none" }}>
                    <Text color="gray" highContrast>
                      {t("membership")}
                    </Text>
                  </Link>
                  <Link to="/volunteer/" style={{ textDecoration: "none" }}>
                    <Text color="gray" highContrast>
                      {t("volunteer")}
                    </Text>
                  </Link>
                </nav>
              </Flex>
            )}
          </Flex>

          <Flex align="center" gap="3">
            <Button variant="ghost" size="1" onClick={toggleLanguage}>
              {i18n.language === "nb" ? "EN" : "NB"}
            </Button>
            <Button variant="ghost" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
              {theme === "light" ? <MoonIcon /> : <SunIcon />}
            </Button>
            {isAuthenticated && user ? (
              <DropdownMenu.Root>
                <DropdownMenu.Trigger>
                  <Button variant="soft">
                    {user.first_name ? `${user.first_name} ${user.last_name}` : user.username}
                    <DropdownMenu.TriggerIcon />
                  </Button>
                </DropdownMenu.Trigger>
                <DropdownMenu.Content>
                  <DropdownMenu.Item onClick={() => navigate("/me/")}>{t("profile")}</DropdownMenu.Item>
                  <DropdownMenu.Separator />
                  <DropdownMenu.Item onClick={handleLogout}>{t("logout")}</DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Root>
            ) : (
              <Flex gap="2">
                <Button variant="soft" asChild>
                  <Link to="/login/">{t("login")}</Link>
                </Button>
                <Button asChild>
                  <Link to="/register/">{t("register")}</Link>
                </Button>
              </Flex>
            )}
          </Flex>
        </Flex>
        <Separator size="4" mt="3" />
      </Container>
    </Box>
  );
}
