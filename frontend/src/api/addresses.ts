import { apiClient } from "./client";

export interface Address {
  id: number;
  user_id: number;
  title: string;
  recipient_name: string;
  phone: string;
  province: string;
  city: string;
  address_line: string;
  postal_code: string;
  is_default: boolean;
}

export interface AddressInput {
  title: string;
  recipient_name: string;
  phone: string;
  province: string;
  city: string;
  address_line: string;
  postal_code: string;
}

export type AddressUpdate = Partial<AddressInput>;

export function getAddresses(token: string) {
  return apiClient<Address[]>("/addresses", { token });
}

export function createAddress(token: string, data: AddressInput) {
  return apiClient<Address>("/addresses", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function updateAddress(
  token: string,
  addressId: number,
  data: AddressUpdate,
) {
  return apiClient<Address>(`/addresses/${addressId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(data),
  });
}

export function setDefaultAddress(token: string, addressId: number) {
  return apiClient<Address>(`/addresses/${addressId}/default`, {
    method: "PATCH",
    token,
  });
}

export function deleteAddress(token: string, addressId: number) {
  return apiClient<void>(`/addresses/${addressId}`, {
    method: "DELETE",
    token,
  });
}
