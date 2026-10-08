import { apiClient } from "./client";

export interface Payment {
  id: number;
  order_id: number;
  amount: number;
  status: string;
  provider: string;
  provider_payment_id: string | null;
}

export function createPayment(token: string, orderId: number) {
  return apiClient<Payment>("/payments", {
    method: "POST",
    token,
    body: JSON.stringify({ order_id: orderId }),
  });
}

export function getPayments(token: string) {
  return apiClient<Payment[]>("/payments", { token });
}

export function getPayment(token: string, paymentId: number) {
  return apiClient<Payment>(`/payments/${paymentId}`, { token });
}
