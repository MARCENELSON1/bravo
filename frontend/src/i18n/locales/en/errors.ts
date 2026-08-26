// Namespace `errors`: user-facing English messages keyed by the backend's stable
// error `code` (see `app/domain/**/exceptions.py`). `apiErrorText` looks up
// `errors.<code>`; any code missing here falls back to the backend's Spanish
// `message`, so this file is the single place that makes the error surface
// English. Keep it in sync as new codes are added to the backend.
export const errors = {
  // Identity / auth
  invalid_credentials: "Incorrect business, email or password.",
  email_not_verified: "You need to verify your email before signing in.",
  email_already_registered: "That email is already registered.",
  invalid_email: "Invalid email.",
  tenant_already_exists: "That business identifier is already taken.",
  tenant_not_found: "Business not found.",
  invalid_token: "The link isn't valid.",
  expired_token: "The link expired. Request a new one.",
  token_already_used: "This link was already used.",
  invalid_invitation: "The invitation isn't valid or has expired.",
  user_locked: "This account is temporarily locked. Try again later.",
  user_not_found: "User not found.",
  inactive_user: "This account is inactive.",
  insufficient_role: "You don't have permission to do that.",

  // Orders
  empty_order: "The order has no items.",
  order_not_found: "Order not found.",
  order_not_invoiceable: "This order can't be invoiced.",
  order_has_authorized_invoice: "This order already has an authorized invoice.",
  invalid_order_transition: "That order can't change to that state.",
  invalid_item_transition: "That item can't change to that state.",
  invalid_item_quantity: "Invalid item quantity.",
  item_not_found: "Item not found.",
  item_not_pending: "That item is no longer pending.",

  // Payments / cash
  invalid_payment_amount: "Invalid payment amount.",
  payment_not_found: "Payment not found.",
  payment_not_refundable: "This payment can't be refunded.",
  payment_gateway_not_connected: "The payment gateway isn't connected.",
  cash_session_already_open: "There's already an open cash session.",
  cash_session_already_closed: "This cash session is already closed.",
  cash_session_not_found: "Cash session not found.",
  no_open_cash_session: "There's no open cash session.",

  // Invoicing / tax
  invoice_not_found: "Invoice not found.",
  tax_gateway_not_connected: "The tax service isn't connected.",
  tax_provider_unavailable: "The tax service is unavailable right now. Try again.",
  invalid_tax_provider_credential: "The tax provider credentials aren't valid.",
  rail_not_allowed_for_region: "That payment method isn't available in your region.",

  // Products / inventory / recipes
  product_not_found: "Product not found.",
  inactive_product: "That product is inactive.",
  ingredient_not_found: "Ingredient not found.",
  supplier_not_found: "Supplier not found.",
  recipe_not_found: "Recipe not found.",
  recipe_cycle: "A recipe can't contain itself.",
  preparation_not_found: "Preparation not found.",
  invalid_recipe_component: "A recipe item must point to an ingredient or a preparation.",
  incompatible_units: "The units aren't compatible.",
  invalid_unit_cost: "Invalid unit cost.",
  invalid_quantity: "Invalid quantity.",

  // Floor / tables / sectors / reservations
  table_not_found: "Table not found.",
  sector_not_found: "Section not found.",
  reservation_not_found: "Reservation not found.",
  invalid_reservation_transition: "That reservation can't change to that state.",
  invalid_party_size: "Invalid party size.",

  // Shifts / time clock / presence
  shift_already_open: "You already have an open shift.",
  shift_already_closed: "This shift is already closed.",
  shift_not_found: "Shift not found.",
  no_open_shift: "You don't have an open shift.",
  invalid_shift_time: "Invalid shift time.",
  presence_disabled: "Clock-in isn't enabled.",
  presence_rate_limited: "Too many attempts. Wait a moment and try again.",
  presence_token_reused: "That clock-in code was already used.",
  invalid_presence_token: "The clock-in code isn't valid.",
  invalid_presence_device: "This device isn't authorized for clock-ins.",

  // Billing / subscription / plans
  subscription_not_found: "Subscription not found.",
  subscription_already_active: "Your subscription is already active.",
  invalid_subscription_transition: "That subscription can't change to that state.",
  invalid_billing_webhook: "Invalid billing notification.",
  invalid_webhook_signature: "The notification signature couldn't be verified.",
  plan_not_found: "Plan not found.",
  invalid_plan_feature: "Invalid plan feature.",

  // Advisor / copilot
  invalid_advisor_settings: "The advisor settings are invalid.",
  copilot_disabled: "The copilot isn't enabled for your business.",
  copilot_query_error: "We couldn't answer that question. Try rephrasing it.",
  unsafe_query: "That request can't be run for safety reasons.",

  // CRM / leads / integrations
  customer_not_found: "Customer not found.",
  invalid_lead: "Invalid data.",
  lead_not_delivered: "We couldn't send your message. Try again.",
  invalid_oauth_state: "The connection couldn't be verified. Try again.",

  // Money / misc
  invalid_money_amount: "Invalid amount.",
  currency_mismatch: "The currencies don't match.",
  unsupported_currency: "Unsupported currency.",
  session_not_found: "Session not found.",
  validation_error: "Please check the highlighted fields.",
} as const
