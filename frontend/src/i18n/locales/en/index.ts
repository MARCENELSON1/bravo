// English (US) barrel. Same namespaces as `es` — one file per feature so the
// dictionaries stay navigable as the app grows.
import { auth } from "./auth"
import { cashier } from "./cashier"
import { common } from "./common"
import { dashboard } from "./dashboard"
import { errors } from "./errors"
import { floor } from "./floor"
import { identity } from "./identity"
import { kds } from "./kds"
import { login } from "./login"
import { orders } from "./orders"
import { reservations } from "./reservations"
import { shell } from "./shell"
import { timeclock } from "./timeclock"

export const en = {
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
} as const
