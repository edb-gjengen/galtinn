import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Button, DropdownMenu, Flex, Text } from "@radix-ui/themes";
import { useAuth } from "@/hooks/useAuth";

export function Navbar() {
  const { t, i18n } = useTranslation();
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login/");
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === "nb" ? "en" : "nb";
    i18n.changeLanguage(newLang);
  };

  return (
    <Box
      style={{
        borderBottom: "1px solid var(--gray-5)",
        backgroundColor: "var(--color-background)",
      }}
      px="4"
      py="3"
    >
      <Flex justify="between" align="center" gap="4">
        <Flex align="center" gap="4">
          <Link to={isAuthenticated ? "/home/" : "/login/"} style={{ textDecoration: "none" }}>
            <Text size="5" weight="bold" color="blue">
              Galtinn
            </Text>
          </Link>

          {isAuthenticated && (
            <Flex gap="3" asChild>
              <nav>
                <Link to="/home/" style={{ textDecoration: "none" }}>
                  <Text color="gray" highContrast>
                    {t("home")}
                  </Text>
                </Link>
                <Link to="/memberships/" style={{ textDecoration: "none" }}>
                  <Text color="gray" highContrast>
                    {t("membership")}
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
    </Box>
  );
}
