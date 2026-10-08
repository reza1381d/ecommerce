import { apiClient } from "./client";

export interface Coupon {
  id: number;
  code: string;
  user_id: number | null;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  max_discount: number | null;
  min_order_amount: number;
  max_uses: number | null;
  max_uses_per_user: number | null;
  used_count: number;
  starts_at: string | null;
  expires_at: string | null;
  is_active: boolean;
}

export interface CouponCreateRequest {
  code: string;
  user_id?: number | null;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  max_discount?: number | null;
  min_order_amount?: number;
  max_uses?: number | null;
  max_uses_per_user?: number | null;
  starts_at?: string | null;
  expires_at?: string | null;
  is_active?: boolean;
}

export type CouponUpdateRequest = Partial<CouponCreateRequest>;

export interface CouponQuote {
  valid: boolean;
  subtotal: number;
  discount_amount: number;
  total_amount: number;
}

export function validateCoupon(token: string, code: string) {
  return apiClient<CouponQuote>("/coupons/validate", {
    method: "POST",
    token,
    body: JSON.stringify({ code }),
  });
}

export function createCoupon(token: string, data: CouponCreateRequest) {
  return apiClient<Coupon>("/coupons", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function getCouponByCode(token: string, code: string) {
  return apiClient<Coupon>(
    `/coupons/code/${encodeURIComponent(code)}`,
    { token },
  );
}

export function updateCoupon(
  token: string,
  couponId: number,
  data: CouponUpdateRequest,
) {
  return apiClient<Coupon>(`/coupons/${couponId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(data),
  });
}
