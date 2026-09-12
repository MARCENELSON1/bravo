// Barrel del idioma español. Un namespace por feature (archivo aparte) para que
// los diccionarios sigan siendo navegables a medida que crece la app. Español es
// el idioma base (paridad): las nuevas pantallas se migran a `t()` de a poco.
import { advisor } from "./advisor"
import { analytics } from "./analytics"
import { auth } from "./auth"
import { billing } from "./billing"
import { cashier } from "./cashier"
import { common } from "./common"
import { copilot } from "./copilot"
import { crm } from "./crm"
import { dashboard } from "./dashboard"
import { errors } from "./errors"
import { expenses } from "./expenses"
import { finance } from "./finance"
import { floor } from "./floor"
import { identity } from "./identity"
import { integrations } from "./integrations"
import { inventory } from "./inventory"
import { invoices } from "./invoices"
import { kds } from "./kds"
import { login } from "./login"
import { orders } from "./orders"
import { platform } from "./platform"
import { products } from "./products"
import { publicMenu } from "./public-menu"
import { reports } from "./reports"
import { reservations } from "./reservations"
import { settings } from "./settings"
import { shell } from "./shell"
import { timeclock } from "./timeclock"

export const es = {
  common,
  login,
  auth,
  identity,
  errors,
  shell,
  dashboard,
  orders,
  floor,
  kds,
  cashier,
  timeclock,
  reservations,
  finance,
  products,
  publicMenu,
  inventory,
  expenses,
  invoices,
  analytics,
  reports,
  advisor,
  copilot,
  crm,
  integrations,
  settings,
  billing,
  platform,
} as const
