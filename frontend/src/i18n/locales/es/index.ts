// Barrel del idioma español. Un namespace por feature (archivo aparte) para que
// los diccionarios sigan siendo navegables a medida que crece la app. Español es
// el idioma base (paridad): las nuevas pantallas se migran a `t()` de a poco.
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
} as const
