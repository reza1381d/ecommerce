import { apiClient } from "./client";

export interface AdminPaymentCustomer {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
}

export interface AdminPayment {
  id: number;
  order_id: number;
  amount: number | string;
  status: string;
  provider: string;
  provider_payment_id: string | null;
  created_at: string;
  order_status: string;
  customer: AdminPaymentCustomer;
}

export interface AdminPaymentsResponse {
  items: AdminPayment[];
  page: number;
  limit: number;
  total: number;
}

export type AdminPaymentSortBy =
  | "id"
  | "order_id"
  | "amount"
  | "status"
  | "provider"
  | "created_at";

export interface GetAdminPaymentsParams {
  page?: number;
  limit?: number;
  search?: string;
  paymentStatus?: string;
  provider?: string;
  orderId?: number;
  sortBy?: AdminPaymentSortBy;
  sortOrder?: "asc" | "desc";
}

export function getAdminPayments(
  token: string,
  params: GetAdminPaymentsParams = {},
) {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    limit: String(params.limit ?? 20),
    sort_by: params.sortBy ?? "created_at",
    sort_order: params.sortOrder ?? "desc",
  });
  if (params.search?.trim()) query.set("search", params.search.trim());
  if (params.paymentStatus) query.set("payment_status", params.paymentStatus);
  if (params.provider) query.set("provider", params.provider);
  if (params.orderId) query.set("order_id", String(params.orderId));

  return apiClient<AdminPaymentsResponse>(
    `/admin/payments?${query.toString()}`,
    { token },
  );
}
