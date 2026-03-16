export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  date_of_birth: string | null;
  place_of_study: number | null;
  street_address: string | null;
  street_address_two: string | null;
  postal_code: string | null;
  city: string | null;
  country: string;
  is_volunteer: boolean;
  is_member: boolean;
  email_is_confirmed: boolean;
  phone_number_confirmed: boolean;
  active_member_card: MemberCard | null;
  last_membership: Membership | null;
  groups: Group[];
  discord_profile: DiscordProfile | null;
  has_set_username: boolean;
  date_joined?: string;
  updated?: string;
}

export interface Membership {
  id: number;
  start_date: string;
  end_date: string | null;
  order: number | null;
  user: number;
  membership_type: string;
  is_valid: boolean;
  expires_in_less_than_one_month?: boolean;
}

export interface MembershipType {
  id: number;
  name: string;
  slug: string;
  price: number;
  price_nok_kr: number;
  description: string;
  is_active: boolean;
  is_default: boolean;
  expiry_type: string;
}

export interface MemberCard {
  card_number: number;
  registered: string | null;
  is_active: boolean;
  user: number | null;
}

export interface Group {
  id: number;
  name: string;
}

export interface DiscordProfile {
  id: number;
  discord_id: string;
  user: number;
}

export interface Order {
  uuid: string;
  price_nok: number;
  price_nok_kr: number;
  payment_method: string;
  payment_method_display: string;
}

export interface OrgUnit {
  id: number;
  name: string;
  slug: string;
  short_name: string;
  is_active: boolean;
  description: string;
  email: string;
  contact_person: OrgUnitUser | null;
  website: string;
  group: number | null;
  admin_group: number | null;
  parent: number | null;
  users: OrgUnitUser[];
  admins: OrgUnitUser[];
}

export interface OrgUnitUser {
  id: number;
  username: string;
}

export interface OrgUnitMember {
  id: number;
  uuid: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_admin: boolean;
  membership_end_date: string | null;
  membership_is_valid: boolean;
}

export interface OrgUnitMembersResponse {
  members: OrgUnitMember[];
  is_admin: boolean;
}

export interface UserSearchResult {
  id: number;
  uuid: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface ApiError {
  detail?: string;
  non_field_errors?: string[];
  [key: string]: unknown;
}
